"""Immich sync service - orchestrates fetch, download, store, record workflow."""

import logging
import random
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import UUID

import sqlalchemy
from private_assistant_commons.database import GlobalDevice
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from private_assistant_picture_display_skill.immich.client import ImmichClient
from private_assistant_picture_display_skill.immich.config import (
    DeviceRequirements,
    ImmichConnectionConfig,
    ImmichSyncConfig,
    MinioWriterConfig,
)
from private_assistant_picture_display_skill.immich.models import ImmichAsset
from private_assistant_picture_display_skill.immich.storage import MinioStorageClient
from private_assistant_picture_display_skill.models.image import Image
from private_assistant_picture_display_skill.models.immich_sync_job import ImmichSyncJob, SyncStrategy
from private_assistant_picture_display_skill.utils.color_analysis import ColorProfileAnalyzer
from private_assistant_picture_display_skill.utils.image_processing import ImageProcessor
from private_assistant_picture_display_skill.utils.metadata_builder import MetadataBuilder


class ProcessResult(Enum):
    """Result of processing a single asset."""

    DOWNLOADED = auto()
    SKIPPED_EXISTING = auto()
    SKIPPED_UNDERSIZED = auto()
    SKIPPED_COLOR_MISMATCH = auto()


@dataclass
class SyncResult:
    """Result of a sync operation."""

    fetched: int = 0
    filtered: int = 0  # After client-side filters
    downloaded: int = 0
    skipped_existing: int = 0
    skipped_undersized: int = 0  # Too small for target dimensions
    skipped_color_mismatch: int = 0  # Color profile incompatible
    stopped_at_limit: bool = False  # True if total image limit was reached
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return True if no errors occurred."""
        return len(self.errors) == 0

    def __str__(self) -> str:
        """Return human-readable summary."""
        limit_info = ", stopped_at_limit=True" if self.stopped_at_limit else ""
        return (
            f"SyncResult(fetched={self.fetched}, filtered={self.filtered}, "
            f"downloaded={self.downloaded}, skipped_existing={self.skipped_existing}, "
            f"skipped_undersized={self.skipped_undersized}, "
            f"skipped_color={self.skipped_color_mismatch}, errors={len(self.errors)}{limit_info})"
        )


class ImmichSyncService:
    """Orchestrates syncing images from Immich to local storage.

    Workflow:
    1. Load active sync jobs from database
    2. For each job, fetch assets from Immich matching filters
    3. Apply client-side filters (orientation, dimensions, color)
    4. Download original file from Immich
    5. Upload to MinIO with path: {prefix}/{asset_id}.{ext}
    6. Create/update Image record in PostgreSQL
    """

    def __init__(
        self,
        engine: AsyncEngine,
        logger: logging.Logger,
        connection_config: ImmichConnectionConfig | None = None,
        sync_config: ImmichSyncConfig | None = None,
        minio_config: MinioWriterConfig | None = None,
    ) -> None:
        """Initialize sync service.

        Args:
            engine: Async database engine
            logger: Logger instance
            connection_config: Immich connection settings (defaults to env vars)
            sync_config: Global sync settings (defaults to env vars)
            minio_config: MinIO writer config (defaults to env vars)

        """
        self.engine = engine
        self.logger = logger

        # Load configs from environment if not provided
        self.connection_config = connection_config or ImmichConnectionConfig()
        self.sync_config = sync_config or ImmichSyncConfig()
        self.minio_config = minio_config or MinioWriterConfig()

        # Initialize clients
        self.immich = ImmichClient(
            config=self.connection_config,
            logger=logger,
        )
        self.storage = MinioStorageClient(
            config=self.minio_config,
            logger=logger,
        )

    async def sync_all_active_jobs(self) -> dict[str, SyncResult]:
        """Execute all active sync jobs from database.

        Returns:
            Dict mapping job name to SyncResult

        """
        results: dict[str, SyncResult] = {}
        total_uploads = 0  # Track uploads across all jobs in this run

        async with AsyncSession(self.engine) as session:
            stmt = select(ImmichSyncJob).where(ImmichSyncJob.is_active == sqlalchemy.true())
            db_result = await session.exec(stmt)
            jobs = list(db_result.all())

        if not jobs:
            self.logger.warning("No active sync jobs found in database")
            return results

        self.logger.info("Found %d active sync jobs", len(jobs))

        # Check total image limit
        max_images = self.sync_config.max_images
        existing_count = await self._count_existing_immich_images()

        if max_images > 0:
            remaining_capacity = max_images - existing_count
            self.logger.info(
                "Existing Immich images: %d, limit: %d, can upload: %d",
                existing_count,
                max_images,
                max(0, remaining_capacity),
            )
            if remaining_capacity <= 0:
                self.logger.warning(
                    "Total image limit reached (%d/%d), skipping all jobs",
                    existing_count,
                    max_images,
                )
                for job in jobs:
                    skip_result = SyncResult()
                    skip_result.stopped_at_limit = True
                    results[job.name] = skip_result
                return results

        self.storage.ensure_bucket_exists()

        async with self.immich.connect():
            for job in jobs:
                # Check if limit reached during this run
                if max_images > 0:
                    remaining = max_images - existing_count - total_uploads
                    if remaining <= 0:
                        self.logger.info(
                            "Skipping job '%s': total image limit (%d) already reached",
                            job.name,
                            max_images,
                        )
                        skip_result = SyncResult()
                        skip_result.stopped_at_limit = True
                        results[job.name] = skip_result
                        continue

                self.logger.info("Processing sync job: %s", job.name)
                try:
                    # Calculate remaining uploads allowed for this job
                    max_uploads_remaining = max_images - existing_count - total_uploads if max_images > 0 else None
                    result = await self._sync_job(job, max_uploads_remaining=max_uploads_remaining)
                    results[job.name] = result
                    total_uploads += result.downloaded
                    self.logger.info("Job '%s' completed: %s", job.name, result)
                except Exception as e:
                    error_result = SyncResult()
                    error_result.errors.append(f"Job failed: {e}")
                    results[job.name] = error_result
                    self.logger.exception("Job '%s' failed", job.name)

        if max_images > 0:
            self.logger.info(
                "Uploaded %d images this run, total Immich images now: %d/%d",
                total_uploads,
                existing_count + total_uploads,
                max_images,
            )

        return results

    async def _sync_job(self, job: ImmichSyncJob, max_uploads_remaining: int | None = None) -> SyncResult:
        """Execute a single sync job.

        Args:
            job: Sync job configuration
            max_uploads_remaining: Maximum uploads allowed for this job (None = unlimited)

        Returns:
            SyncResult with counts and any errors

        """
        result = SyncResult()

        # Get device requirements (always required)
        device_reqs = await self._get_device_requirements(job.target_device_id)

        # Calculate fetch count (overfetch for client-side orientation/dimension filters)
        fetch_count = job.count * job.overfetch_multiplier

        strategy_desc = f"smart search (query='{job.query}')" if job.strategy == SyncStrategy.SMART else "random"
        self.logger.info(
            "Fetching %d images via %s for job '%s' (overfetch x%d for client-side filters)",
            fetch_count,
            strategy_desc,
            job.name,
            job.overfetch_multiplier,
        )

        try:
            # Route to appropriate search method based on strategy
            if job.strategy == SyncStrategy.SMART:
                assets = await self.immich.search_smart(job, count_override=fetch_count)
                # Optionally random-pick from smart search results
                if job.random_pick and len(assets) > job.count:
                    assets = random.sample(assets, job.count)
                    self.logger.info("Randomly picked %d assets from smart search results", len(assets))
            else:
                assets = await self.immich.search_random(job, count_override=fetch_count)

            result.fetched = len(assets)
            self.logger.info("Fetched %d assets from Immich", result.fetched)
        except Exception as e:
            result.errors.append(f"Failed to fetch assets: {e}")
            self.logger.exception("Failed to fetch assets from Immich")
            return result

        # Apply client-side filters (orientation, dimensions)
        assets = self._filter_assets(assets, job, device_reqs)
        result.filtered = len(assets)
        if len(assets) < job.count:
            self.logger.warning(
                "Only %d images matched client-side filters (requested %d). "
                "Consider increasing overfetch_multiplier or relaxing filters.",
                len(assets),
                job.count,
            )
        else:
            self.logger.info("Filtered to %d assets matching criteria", len(assets))

        # Process each asset
        for asset in assets:
            # Check if upload limit reached mid-job
            if max_uploads_remaining is not None and result.downloaded >= max_uploads_remaining:
                self.logger.info(
                    "Stopping job '%s': reached total image limit (downloaded %d in this job)",
                    job.name,
                    result.downloaded,
                )
                result.stopped_at_limit = True
                break

            try:
                process_result = await self._process_asset(asset, job, device_reqs)
                self._update_result_counters(result, process_result)
            except Exception as e:
                error_msg = f"Failed to process asset {asset.id}: {e}"
                result.errors.append(error_msg)
                self.logger.exception("Failed to process asset %s", asset.id)

        return result

    @staticmethod
    def _update_result_counters(result: SyncResult, process_result: ProcessResult) -> None:
        """Update result counters based on process result."""
        if process_result == ProcessResult.DOWNLOADED:
            result.downloaded += 1
        elif process_result == ProcessResult.SKIPPED_EXISTING:
            result.skipped_existing += 1
        elif process_result == ProcessResult.SKIPPED_UNDERSIZED:
            result.skipped_undersized += 1
        elif process_result == ProcessResult.SKIPPED_COLOR_MISMATCH:
            result.skipped_color_mismatch += 1

    async def _get_device_requirements(self, device_id: UUID) -> DeviceRequirements:
        """Get display requirements from global device table.

        Args:
            device_id: UUID of target device

        Returns:
            DeviceRequirements with width, height, and orientation

        Raises:
            ValueError: If device not found or missing required display attributes

        """
        async with AsyncSession(self.engine) as session:
            # Query global_devices table (from private-assistant-commons)
            # AIDEV-NOTE: global_devices uses device_attributes JSON for display specs
            result = await session.exec(select(GlobalDevice).where(GlobalDevice.id == device_id))
            device = result.first()

        if not device:
            raise ValueError(f"Target device not found: {device_id}")

        # Extract device_attributes JSON
        attrs: dict[str, Any] = device.device_attributes or {}

        width = attrs.get("display_width")
        height = attrs.get("display_height")
        orientation = attrs.get("orientation")

        if not width or not height or not orientation:
            raise ValueError(
                f"Device {device_id} missing required display attributes. "
                f"Got: width={width}, height={height}, orientation={orientation}"
            )

        return DeviceRequirements(
            width=width,
            height=height,
            orientation=orientation,
            display_model=attrs.get("model"),
        )

    async def _process_asset(
        self,
        asset: ImmichAsset,
        job: ImmichSyncJob,
        device_reqs: DeviceRequirements,
    ) -> ProcessResult:
        """Process a single asset: download, store, record.

        Args:
            asset: Immich asset to process
            job: Sync job configuration
            device_reqs: Target device display requirements

        Returns:
            ProcessResult indicating what happened

        """
        source_url = self._build_source_url(asset.id)

        # Check for existing record
        if self.sync_config.skip_existing:
            existing = await self._find_existing_image(source_url)
            if existing:
                self.logger.debug("Skipping existing asset: %s", asset.id)
                return ProcessResult.SKIPPED_EXISTING

        # Target dimensions from device requirements (always processed to jpg)
        target_width = device_reqs.width
        target_height = device_reqs.height
        storage_path = f"{self.sync_config.storage_prefix}/{asset.id}.jpg"

        # Check if already in MinIO (in case DB record was lost)
        if self.storage.object_exists(storage_path):
            self.logger.debug("Object already in MinIO: %s", storage_path)
        else:
            # Download original
            self.logger.info("Downloading asset: %s", asset.id)
            image_bytes = await self._collect_stream(self.immich.download_original(asset.id))

            # Check color compatibility (before resize/crop for accurate scoring)
            min_score = job.min_color_score
            if min_score > 0:
                score = ColorProfileAnalyzer.calculate_compatibility_score(image_bytes)
                if score < min_score:
                    self.logger.info("Skipping asset %s: color score %.2f < %.2f", asset.id, score, min_score)
                    return ProcessResult.SKIPPED_COLOR_MISMATCH
                self.logger.debug("Asset %s color score: %.2f", asset.id, score)

            # Process to target dimensions
            self.logger.debug("Processing image to %dx%d", target_width, target_height)
            processed = ImageProcessor.process_for_display(
                image_bytes,
                target_width,
                target_height,
            )
            if processed is None:
                self.logger.info("Skipping asset %s: too small for target dimensions", asset.id)
                return ProcessResult.SKIPPED_UNDERSIZED
            image_bytes = processed

            # Upload to MinIO
            self.storage.upload_from_bytes(
                object_path=storage_path,
                data=image_bytes,
                content_type="image/jpeg",
            )

        # Create database record with processed dimensions
        await self._upsert_image_record(
            asset, storage_path, source_url, job.name, processed_dimensions=(target_width, target_height)
        )

        return ProcessResult.DOWNLOADED

    async def _find_existing_image(self, source_url: str) -> Image | None:
        """Find existing image by source URL."""
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(Image).where(Image.source_url == source_url))
            return result.first()

    async def _count_existing_immich_images(self) -> int:
        """Count images already synced from Immich.

        Returns:
            Number of images with source_url starting with 'immich://'

        """
        async with AsyncSession(self.engine) as session:
            result = await session.exec(
                select(sqlalchemy.func.count()).select_from(Image).where(Image.source_url.like("immich://%"))  # type: ignore[union-attr]
            )
            return result.one()

    async def _upsert_image_record(
        self,
        asset: ImmichAsset,
        storage_path: str,
        source_url: str,
        source_name: str,
        processed_dimensions: tuple[int, int],
    ) -> None:
        """Create or update Image record in database."""
        async with AsyncSession(self.engine) as session:
            # Check for existing record
            result = await session.exec(select(Image).where(Image.source_url == source_url))
            existing = result.first()

            if existing:
                image = existing
            else:
                image = Image(
                    source_name=source_name,
                    storage_path=storage_path,
                    source_url=source_url,
                )
                session.add(image)

            # Set/update metadata with natural language descriptions
            await self._populate_image_from_asset(image, asset)

            # Set processed dimensions (post-crop, what's actually stored in MinIO)
            image.original_width = processed_dimensions[0]
            image.original_height = processed_dimensions[1]

            await session.commit()
            await session.refresh(image)
            self.logger.debug("Saved image record: %s", image.id)

    async def _populate_image_from_asset(self, image: Image, asset: ImmichAsset) -> None:
        """Populate Image fields from Immich asset with natural language metadata."""
        people_names = [p.name for p in (asset.people or []) if p.name]

        city = state = country = None
        date = asset.file_created_at
        if asset.exif_info:
            city = asset.exif_info.city
            state = asset.exif_info.state
            country = asset.exif_info.country
            date = asset.exif_info.date_time_original or date

        album_names = await self._get_asset_album_names(asset.id)

        image.title = MetadataBuilder.build_title(
            people=people_names if people_names else None,
            city=city,
            country=country,
            date=date,
        )
        image.description = MetadataBuilder.build_description(
            people=people_names if people_names else None,
            city=city,
            state=state,
            country=country,
            date=date,
            album_names=album_names if album_names else None,
        )
        image.tags = self._build_tags(city, country, asset.is_favorite, asset.people)

    async def _get_asset_album_names(self, asset_id: str) -> list[str]:
        """Fetch album names for an asset."""
        try:
            albums = await self.immich.get_asset_albums(asset_id)
            return [a.album_name for a in albums]
        except Exception:
            self.logger.debug("Could not fetch albums for asset %s", asset_id)
            return []

    @staticmethod
    def _build_tags(
        city: str | None,
        country: str | None,
        is_favorite: bool,
        people: list | None,
    ) -> str | None:
        """Build comma-separated tags from metadata."""
        tags: list[str] = []
        if city:
            tags.append(city)
        if country:
            tags.append(country)
        if is_favorite:
            tags.append("favorite")
        if people:
            tags.extend(person.name for person in people if person.name)
        return ",".join(tags) if tags else None

    def _filter_assets(
        self,
        assets: list[ImmichAsset],
        job: ImmichSyncJob,
        device_reqs: DeviceRequirements,
    ) -> list[ImmichAsset]:
        """Filter assets by orientation and dimensions (client-side).

        Args:
            assets: List of assets from Immich
            job: Sync job configuration
            device_reqs: Target device display requirements

        Returns:
            Filtered list limited to job.count

        """
        filtered: list[ImmichAsset] = []

        for asset in assets:
            if not asset.exif_info:
                self.logger.debug("Skipping asset %s: no EXIF data", asset.id)
                continue

            width = asset.exif_info.exif_image_width
            height = asset.exif_info.exif_image_height
            if not width or not height:
                self.logger.debug("Skipping asset %s: missing dimensions in EXIF", asset.id)
                continue

            # Orientation check from device requirements
            if not self._matches_orientation(width, height, device_reqs.orientation):
                continue

            # Dimension checks from device requirements
            if width < device_reqs.width or height < device_reqs.height:
                continue

            filtered.append(asset)

            if len(filtered) >= job.count:
                break

        return filtered

    @staticmethod
    def _matches_orientation(width: int, height: int, orientation: str) -> bool:
        """Check if dimensions match the requested orientation."""
        if orientation == "landscape":
            return width > height
        if orientation == "portrait":
            return height > width
        if orientation == "square":
            return width == height
        return True

    @staticmethod
    async def _collect_stream(stream: AsyncIterator[bytes]) -> bytes:
        """Collect async byte stream into a single bytes object."""
        chunks: list[bytes] = []
        async for chunk in stream:
            chunks.append(chunk)
        return b"".join(chunks)

    def _build_source_url(self, asset_id: str) -> str:
        """Build unique source URL for deduplication."""
        return f"immich://{asset_id}"
