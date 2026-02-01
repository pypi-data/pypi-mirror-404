"""Image queue management and selection service."""

import logging
from datetime import datetime
from uuid import UUID

from private_assistant_commons.database import GlobalDevice
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from private_assistant_picture_display_skill.config import PictureSkillConfig
from private_assistant_picture_display_skill.models.commands import DisplayCommand
from private_assistant_picture_display_skill.models.device import DeviceDisplayState
from private_assistant_picture_display_skill.models.image import Image
from private_assistant_picture_display_skill.services.device_mqtt_client import DeviceMqttClient


class ImageManager:
    """Manages image queue and selection for display devices.

    Implements FIFO image selection with device compatibility filtering.
    Images are selected based on when they were last displayed, with
    never-displayed images taking priority.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        device_mqtt: DeviceMqttClient,
        skill_config: PictureSkillConfig,
        logger: logging.Logger,
    ) -> None:
        """Initialize the image manager.

        Args:
            engine: Async database engine
            device_mqtt: Device MQTT client for commands
            skill_config: Skill configuration
            logger: Logger instance from parent skill

        """
        self.engine = engine
        self.device_mqtt = device_mqtt
        self.skill_config = skill_config
        self.logger = logger

    async def get_next_image_for_device(self, device: GlobalDevice) -> Image | None:
        """Select next image using FIFO algorithm with device compatibility.

        Selection criteria:
        1. Images never displayed (last_displayed_at IS NULL) first
        2. Then by least recently displayed (last_displayed_at ASC)
        3. Filtered by device dimensions (image must fit)

        Args:
            device: GlobalDevice with device_attributes containing display dimensions

        Returns:
            Next image to display, or None if no suitable images available

        """
        # Extract display dimensions from device_attributes
        attrs = device.device_attributes or {}
        display_width = attrs.get("display_width")
        display_height = attrs.get("display_height")

        # Device must have both dimensions set
        if display_width is None or display_height is None:
            self.logger.warning("Device %s missing display dimensions, skipping", device.name)
            return None

        async with AsyncSession(self.engine) as session:
            # Build query - require exact dimension match
            query = select(Image).where(
                col(Image.original_width) == display_width,
                col(Image.original_height) == display_height,
            )

            # Order by FIFO (nulls first = never displayed)
            query = query.order_by(col(Image.last_displayed_at).asc().nullsfirst()).limit(1)

            result = await session.exec(query)
            return result.first()

    async def send_display_command(self, device: GlobalDevice, image: Image) -> None:
        """Send display command to device and update state.

        Args:
            device: GlobalDevice to send command to
            image: Image to display

        """
        # Create display command
        command = DisplayCommand(
            action="display",
            image_path=image.storage_path,
            image_id=str(image.id),
            title=image.title,
        )

        # Publish command to device (use device.name as topic identifier)
        await self.device_mqtt.publish_command(device.name, command)

        # Update database state
        await self._update_display_state(device.id, image)

        self.logger.info(
            "Sent display command to %s for image %s (%s)",
            device.name,
            image.id,
            image.title or "untitled",
        )

    async def _update_display_state(self, global_device_id: UUID, image: Image) -> None:
        """Update database after sending display command.

        Args:
            global_device_id: GlobalDevice UUID that received the command
            image: Image being displayed

        """
        now = datetime.now()

        async with AsyncSession(self.engine) as session:
            # Update image last displayed time
            image_result = await session.exec(select(Image).where(Image.id == image.id))
            db_image = image_result.first()
            if db_image:
                db_image.last_displayed_at = now

            # Update device display state
            state_result = await session.exec(
                select(DeviceDisplayState).where(DeviceDisplayState.global_device_id == global_device_id)
            )
            display_state = state_result.first()

            if display_state:
                display_state.current_image_id = image.id
                display_state.displayed_since = now
                # Schedule next display based on default duration
                display_state.scheduled_next_at = datetime.fromtimestamp(
                    now.timestamp() + self.skill_config.default_display_duration
                )
            else:
                # Create display state if it doesn't exist
                display_state = DeviceDisplayState(
                    global_device_id=global_device_id,
                    current_image_id=image.id,
                    displayed_since=now,
                    scheduled_next_at=datetime.fromtimestamp(
                        now.timestamp() + self.skill_config.default_display_duration
                    ),
                )
                session.add(display_state)

            await session.commit()

    async def get_current_image_for_device(self, global_device_id: UUID) -> Image | None:
        """Get the currently displayed image for a device.

        Args:
            global_device_id: GlobalDevice UUID

        Returns:
            Currently displayed image, or None if not displaying

        """
        async with AsyncSession(self.engine) as session:
            # Get display state
            state_result = await session.exec(
                select(DeviceDisplayState).where(DeviceDisplayState.global_device_id == global_device_id)
            )
            display_state = state_result.first()

            if display_state is None or display_state.current_image_id is None:
                return None

            # Get the image
            image_result = await session.exec(select(Image).where(Image.id == display_state.current_image_id))
            return image_result.first()
