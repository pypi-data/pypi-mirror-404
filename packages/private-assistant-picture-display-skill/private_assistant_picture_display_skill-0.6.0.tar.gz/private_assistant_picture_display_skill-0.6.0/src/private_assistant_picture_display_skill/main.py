"""CLI entrypoint for the Picture Display Skill."""

import asyncio
import pathlib
from typing import Annotated

import jinja2
import sqlalchemy
import typer
from private_assistant_commons import (
    MqttConfig,
    create_skill_engine,
    mqtt_connection_handler,
    skill_config,
    skill_logger,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from private_assistant_picture_display_skill.config import PictureSkillConfig
from private_assistant_picture_display_skill.immich import ImmichSyncService
from private_assistant_picture_display_skill.models.device import DeviceDisplayState
from private_assistant_picture_display_skill.models.image import Image
from private_assistant_picture_display_skill.models.immich_sync_job import ImmichSyncJob
from private_assistant_picture_display_skill.picture_skill import PictureSkill

app = typer.Typer(help="Picture Display Skill for Inky e-ink devices")


@app.command()
def main(config_path: Annotated[pathlib.Path, typer.Argument(envvar="PRIVATE_ASSISTANT_CONFIG_PATH")]) -> None:
    """Run the Picture Display Skill.

    Args:
        config_path: Path to YAML configuration file or directory

    """
    asyncio.run(start_skill(config_path))


async def start_skill(config_path: pathlib.Path) -> None:
    """Start the Picture Display Skill with all required services.

    Args:
        config_path: Path to YAML configuration file or directory

    """
    # Set up logger early on
    logger = skill_logger.SkillLogger.get_logger("Private Assistant PictureSkill")

    # Load configuration from YAML
    config_obj = skill_config.load_config(config_path, PictureSkillConfig)

    # Create async database engine with connection pooling and resilience
    # AIDEV-NOTE: create_skill_engine uses PostgresConfig from env (POSTGRES_*) and adds pool_pre_ping, pool_recycle
    db_engine_async = create_skill_engine()

    # Create only skill-specific tables, not all SQLModel metadata
    # AIDEV-NOTE: Global device registry tables are managed by BaseSkill and commons
    async with db_engine_async.begin() as conn:
        # __table__ is a SQLAlchemy runtime attribute that mypy doesn't recognize
        for table in [Image.__table__, DeviceDisplayState.__table__]:  # type: ignore[attr-defined]
            await conn.run_sync(table.create, checkfirst=True)

    logger.info("Database tables initialized for Picture Display Skill")

    # Set up Jinja2 template environment
    template_env = jinja2.Environment(
        loader=jinja2.PackageLoader("private_assistant_picture_display_skill", "templates"),
        autoescape=True,
    )

    # Start the skill using the async MQTT connection handler
    # AIDEV-NOTE: mqtt_connection_handler manages MQTT lifecycle with auto-reconnect
    mqtt_config = MqttConfig()
    await mqtt_connection_handler.mqtt_connection_handler(
        PictureSkill,
        config_obj,
        mqtt_config=mqtt_config,
        retry_interval=5,
        logger=logger,
        template_env=template_env,
        engine=db_engine_async,
    )


@app.command()
def immich_sync(
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show jobs that would be synced")] = False,
) -> None:
    """Sync images from Immich to local storage.

    Executes all active sync jobs from the database. Each job defines filters
    and selection criteria for fetching images from Immich.

    Configuration is via environment variables:
    - IMMICH_BASE_URL: Immich server URL
    - IMMICH_API_KEY: API key for authentication
    - MINIO_WRITER_*: MinIO connection for image storage
    - POSTGRES_*: Database connection (from commons)
    """
    results = asyncio.run(run_immich_sync(dry_run))
    typer.Exit(code=results)


async def run_immich_sync(dry_run: bool) -> int:
    """Run the Immich sync operation for all active jobs.

    Args:
        dry_run: If True, only show what would be synced

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    logger = skill_logger.SkillLogger.get_logger("Immich Sync")

    # Create database engine
    db_engine = create_skill_engine()

    # Ensure required tables exist
    async with db_engine.begin() as conn:
        for table in [Image.__table__, ImmichSyncJob.__table__]:  # type: ignore[attr-defined]
            await conn.run_sync(table.create, checkfirst=True)

    if dry_run:
        async with AsyncSession(db_engine) as session:
            stmt = select(ImmichSyncJob).where(ImmichSyncJob.is_active == sqlalchemy.true())
            db_result = await session.exec(stmt)
            jobs = list(db_result.all())

        if not jobs:
            logger.warning("No active sync jobs found")
            return 0

        logger.info("Dry run mode - would process %d job(s):", len(jobs))
        for job in jobs:
            logger.info("  - %s: strategy=%s, count=%d", job.name, job.strategy, job.count)
        return 0

    # Run sync for all active jobs
    sync_service = ImmichSyncService(
        engine=db_engine,
        logger=logger,
    )

    results = await sync_service.sync_all_active_jobs()

    # Return non-zero exit code if any job had errors
    has_errors = any(not r.success for r in results.values())
    return 1 if has_errors else 0


if __name__ == "__main__":
    app()
