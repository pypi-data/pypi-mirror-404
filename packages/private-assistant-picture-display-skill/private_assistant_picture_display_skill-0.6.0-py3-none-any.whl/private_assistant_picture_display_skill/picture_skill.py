"""Picture Display Skill for controlling Inky e-ink displays."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

import jinja2
from private_assistant_commons import BaseSkill, IntentRequest, IntentType
from private_assistant_commons.database import GlobalDevice
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    import logging
    from uuid import UUID

    import aiomqtt
    from sqlalchemy.ext.asyncio import AsyncEngine

from private_assistant_picture_display_skill.config import DeviceMqttConfig, MinioConfig, PictureSkillConfig
from private_assistant_picture_display_skill.models.commands import (
    DeviceAcknowledge,
    DeviceRegistration,
    RegistrationResponse,
)
from private_assistant_picture_display_skill.models.device import DeviceDisplayState
from private_assistant_picture_display_skill.services.device_mqtt_client import DeviceMqttClient
from private_assistant_picture_display_skill.services.image_manager import ImageManager


class PictureSkill(BaseSkill):
    """Voice-controlled picture display skill for Inky e-ink devices.

    Handles voice commands to control image display on Inky devices:
    - "next picture" / "show next" - Display next image in queue
    - "what am I seeing?" / "describe this picture" - Describe current image

    The skill connects to two MQTT brokers:
    1. Internal MQTT (via BaseSkill): For intent engine communication
    2. Device MQTT (authenticated): For Inky device communication
    """

    # Help text for the skill (automatically stored in database)
    help_text = (
        "You can control the picture display with these commands. "
        'Say "next picture" to show the next image. '
        'Say "what am I seeing" to hear a description of the current picture.'
    )

    # Class attribute for rotation check interval (seconds) - can be overridden in tests
    rotation_check_interval: int = 30

    def __init__(  # noqa: PLR0913
        self,
        config_obj: PictureSkillConfig,
        mqtt_client: aiomqtt.Client,
        task_group: asyncio.TaskGroup,
        engine: AsyncEngine,
        logger: logging.Logger | None = None,
        template_env: jinja2.Environment | None = None,
    ) -> None:
        """Initialize the Picture Display Skill.

        Args:
            config_obj: Skill configuration (inherits from SkillConfig)
            mqtt_client: Internal MQTT client (from BaseSkill)
            task_group: Asyncio task group for concurrent operations
            engine: Async database engine
            logger: Optional custom logger
            template_env: Jinja2 template environment for voice responses

        """
        super().__init__(
            config_obj=config_obj,
            mqtt_client=mqtt_client,
            task_group=task_group,
            engine=engine,
            certainty_threshold=0.7,
            logger=logger,
        )

        # Store skill-specific config
        self.skill_config = config_obj

        # Load device MQTT and MinIO configs from environment
        # AIDEV-NOTE: These use pydantic-settings with env prefixes (DEVICE_MQTT_*, MINIO_*)
        self.device_mqtt_config = DeviceMqttConfig()
        self.minio_config = MinioConfig()

        # Configure supported intents with confidence thresholds
        self.supported_intents = {
            IntentType.MEDIA_NEXT: 0.8,  # "next picture", "show next", "skip"
            IntentType.DEVICE_QUERY: 0.7,  # "what am I seeing?", "describe this"
        }

        # Device type for global registry
        self.supported_device_types = ["picture_display"]

        # Use provided template environment or create default
        if template_env is not None:
            self.template_env = template_env
        else:
            self.template_env = jinja2.Environment(
                loader=jinja2.PackageLoader("private_assistant_picture_display_skill", "templates"),
                autoescape=True,
            )

        # Services - initialized in skill_preparations
        self.device_mqtt: DeviceMqttClient | None = None
        self.image_manager: ImageManager | None = None

    async def skill_preparations(self) -> None:
        """Initialize services after MQTT setup."""
        await super().skill_preparations()

        # Initialize device MQTT client
        self.device_mqtt = DeviceMqttClient(self.device_mqtt_config, self.logger)

        # Start device MQTT as background task
        # AIDEV-NOTE: mqtt_connection_handler doesn't know about our second MQTT, so we manage it here
        self.add_task(self.start_device_mqtt(), name="device_mqtt")

        self.logger.info("Picture skill preparations complete")

    async def start_device_mqtt(self) -> None:
        """Start the device MQTT connection and message listener.

        Runs the device MQTT connection as a background task with
        auto-reconnect behavior.
        """
        if self.device_mqtt is None:
            raise RuntimeError("Device MQTT client not initialized")

        async with self.device_mqtt.connect():
            # Initialize services that depend on MQTT
            self.image_manager = ImageManager(
                engine=self.engine,
                device_mqtt=self.device_mqtt,
                skill_config=self.skill_config,
                logger=self.logger,
            )

            # Start automatic image rotation scheduler
            self.add_task(self._start_rotation_scheduler(), name="image_rotation")

            # Subscribe to device topics
            await self.device_mqtt.subscribe_device_topics()

            # Start listening for device messages
            await self._listen_device_mqtt()

    async def _listen_device_mqtt(self) -> None:
        """Listen for incoming device MQTT messages."""
        if self.device_mqtt is None:
            raise RuntimeError("Device MQTT client not initialized")

        async for message in self.device_mqtt.messages():
            try:
                await self._handle_device_message(message)
            except Exception as e:
                self.logger.error("Error handling device message: %s", e, exc_info=True)

    async def _handle_device_message(self, message: aiomqtt.Message) -> None:
        """Route device MQTT message to appropriate handler.

        Args:
            message: Incoming MQTT message

        """
        if self.device_mqtt is None:
            return

        topic = str(message.topic)
        payload = self.device_mqtt.decode_payload(message.payload)

        if payload is None:
            self.logger.warning("Failed to decode device message payload")
            return

        if topic == self.device_mqtt.REGISTER_TOPIC:
            await self._handle_registration(payload)
        elif "/status" in topic:
            device_id = self.device_mqtt.extract_device_id_from_topic(topic)
            if device_id:
                await self._handle_acknowledge(device_id, payload)

    async def _handle_registration(self, payload: dict) -> None:
        """Handle device registration request.

        Registers device in GlobalDevice registry and creates DeviceDisplayState.

        Args:
            payload: Registration payload from device

        """
        if self.device_mqtt is None:
            self.logger.error("Device MQTT client not initialized")
            return

        try:
            registration = DeviceRegistration.model_validate(payload)
        except ValidationError as e:
            self.logger.error("Invalid registration payload: %s", e)
            return

        # Build device_attributes with display hardware info
        device_attributes = {
            "display_width": registration.display.width,
            "display_height": registration.display.height,
            "orientation": registration.display.orientation,
            "model": registration.display.model,
        }

        # Build pattern list for voice command matching
        patterns = [
            registration.device_id,
            f"{registration.device_id} display",
            f"{registration.device_id} frame",
        ]
        if registration.room:
            patterns.extend(
                [
                    f"{registration.room} display",
                    f"{registration.room} picture frame",
                    f"display in {registration.room}",
                ]
            )

        # Check if device already exists
        existing_device = self._find_device_by_name(registration.device_id)

        if existing_device:
            # Update existing device
            global_device_id = await self._update_device(existing_device.id, device_attributes, patterns)
            status: str = "updated"
            self.logger.info("Updated device registration: %s", registration.device_id)
        else:
            # Register new device in global registry
            global_device_id = await self.register_device(
                device_type="picture_display",
                name=registration.device_id,
                pattern=patterns,
                room=registration.room,
                device_attributes=device_attributes,
            )
            status = "registered"
            self.logger.info("New device registered: %s", registration.device_id)

        # Create/update DeviceDisplayState
        await self._ensure_display_state(global_device_id)

        # Send registration response with MinIO credentials
        response = RegistrationResponse(
            status=status,  # type: ignore[arg-type]
            minio_endpoint=self.minio_config.endpoint,
            minio_bucket=self.minio_config.bucket,
            minio_access_key=self.minio_config.reader_access_key,
            minio_secret_key=self.minio_config.reader_secret_key,
            minio_secure=self.minio_config.secure,
        )
        await self.device_mqtt.publish_registered(registration.device_id, response)

    def _find_device_by_name(self, name: str) -> GlobalDevice | None:
        """Find a device in the global_devices cache by name.

        Args:
            name: Device name to search for

        Returns:
            GlobalDevice if found, None otherwise

        """
        device: GlobalDevice
        for device in self.global_devices:
            if device.name == name:
                return device
        return None

    async def _update_device(self, device_id: UUID, device_attributes: dict, patterns: list[str]) -> UUID:
        """Update an existing device's attributes and patterns.

        Args:
            device_id: GlobalDevice UUID
            device_attributes: New device attributes
            patterns: New pattern list

        Returns:
            The device UUID

        """
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(GlobalDevice).where(GlobalDevice.id == device_id))
            device = result.first()
            if device:
                device.device_attributes = device_attributes
                device.pattern = patterns
                await session.commit()

        # Refresh local device cache
        self.global_devices = await self.get_skill_devices()

        return device_id

    async def _ensure_display_state(self, global_device_id: UUID) -> None:
        """Ensure DeviceDisplayState exists for a device.

        Creates the state record if it doesn't exist, sets is_online=True.

        Args:
            global_device_id: GlobalDevice UUID

        """
        async with AsyncSession(self.engine) as session:
            result = await session.exec(
                select(DeviceDisplayState).where(DeviceDisplayState.global_device_id == global_device_id)
            )
            display_state = result.first()

            if display_state:
                display_state.is_online = True
            else:
                display_state = DeviceDisplayState(
                    global_device_id=global_device_id,
                    is_online=True,
                )
                session.add(display_state)

            await session.commit()

    async def _handle_acknowledge(self, device_name: str, payload: dict) -> None:
        """Handle device acknowledgment after display command.

        Args:
            device_name: Device name from topic
            payload: Acknowledgment payload from device

        """
        try:
            ack = DeviceAcknowledge.model_validate(payload)
        except ValidationError as e:
            self.logger.error("Invalid acknowledge payload from %s: %s", device_name, e)
            return

        # Find device by name
        device = self._find_device_by_name(device_name)
        if device is None:
            self.logger.warning("Acknowledge from unknown device: %s", device_name)
            return

        if not ack.successful_display_change:
            self.logger.warning(
                "Device %s failed to display image: %s",
                device_name,
                ack.error or "unknown error",
            )

        self.logger.debug("Processed acknowledge for device: %s", device_name)

    async def process_request(self, intent_request: IntentRequest) -> None:
        """Process voice command intent.

        Args:
            intent_request: Validated intent request

        """
        intent_type = intent_request.classified_intent.intent_type

        match intent_type:
            case IntentType.MEDIA_NEXT:
                await self._handle_media_next(intent_request)
            case IntentType.DEVICE_QUERY:
                await self._handle_query_status(intent_request)
            case _:
                self.logger.warning("Unhandled intent type: %s", intent_type)

    async def _select_device_for_request(self, intent_request: IntentRequest) -> GlobalDevice | None:
        """Select appropriate device based on room or explicit naming.

        Priority:
        1. Explicitly named device in entities
        2. Device in same room as request
        3. First online device (fallback)

        Args:
            intent_request: Intent request with client info and entities

        Returns:
            Selected GlobalDevice or None if no suitable device found

        """
        device: GlobalDevice  # Type annotation for loop variable

        # Check for explicit device name in entities
        device_entities = intent_request.classified_intent.entities.get("device", [])
        if device_entities:
            device_name = device_entities[0].normalized_value
            # Search in global_devices cache for pattern match
            for device in self.global_devices:
                if device_name.lower() in [p.lower() for p in device.pattern] and await self._is_device_online(
                    device.id
                ):
                    self.logger.debug("Selected device by name: %s", device.name)
                    return device

        # Room-based selection using global device registry
        request_room = intent_request.client_request.room
        if request_room:
            for device in self.global_devices:
                if device.room and device.room.name == request_room and await self._is_device_online(device.id):
                    self.logger.debug("Selected device by room: %s (room: %s)", device.name, request_room)
                    return device

        # Fallback: first online device
        for device in self.global_devices:
            if await self._is_device_online(device.id):
                self.logger.debug("Selected first online device: %s", device.name)
                return device

        return None

    async def _is_device_online(self, global_device_id: UUID) -> bool:
        """Check if a device is online.

        Args:
            global_device_id: GlobalDevice UUID

        Returns:
            True if device is online, False otherwise

        """
        async with AsyncSession(self.engine) as session:
            result = await session.exec(
                select(DeviceDisplayState).where(DeviceDisplayState.global_device_id == global_device_id)
            )
            display_state = result.first()
            return display_state is not None and display_state.is_online

    async def _handle_media_next(self, intent_request: IntentRequest) -> None:
        """Handle 'next picture' command.

        Args:
            intent_request: Intent request with client info

        """
        if self.image_manager is None:
            await self.send_response(
                "Picture display service is not ready. Please try again later.",
                intent_request.client_request,
            )
            return

        # Select device using room-based or explicit naming
        device = await self._select_device_for_request(intent_request)
        if device is None:
            await self.send_response(
                "No picture displays are currently online.",
                intent_request.client_request,
            )
            return

        # Get next image
        image = await self.image_manager.get_next_image_for_device(device)
        if image is None:
            await self.send_response(
                "No images available to display.",
                intent_request.client_request,
            )
            return

        # Send display command
        await self.image_manager.send_display_command(device, image)

        # Send voice response
        template = self.template_env.get_template("next_picture.j2")
        response_text = template.render(image=image)
        await self.send_response(response_text, intent_request.client_request)

    async def _handle_query_status(self, intent_request: IntentRequest) -> None:
        """Handle 'what am I seeing?' command.

        Args:
            intent_request: Intent request with client info

        """
        if self.image_manager is None:
            await self.send_response(
                "Picture display service is not ready.",
                intent_request.client_request,
            )
            return

        # Select device using room-based or explicit naming
        device = await self._select_device_for_request(intent_request)
        if device is None:
            await self.send_response(
                "No picture displays are currently online.",
                intent_request.client_request,
            )
            return

        # Get current image
        image = await self.image_manager.get_current_image_for_device(device.id)
        if image is None:
            await self.send_response(
                "No image is currently being displayed.",
                intent_request.client_request,
            )
            return

        # Send voice response with image description
        template = self.template_env.get_template("describe_image.j2")
        response_text = template.render(image=image)
        await self.send_response(response_text, intent_request.client_request)

    async def _start_rotation_scheduler(self) -> None:
        """Background task for automatic image rotation.

        Periodically checks for devices where scheduled_next_at has passed
        and rotates to the next image.
        """
        while True:
            await asyncio.sleep(self.rotation_check_interval)

            if self.image_manager is None:
                continue

            try:
                await self._rotate_due_devices()
            except Exception as e:
                self.logger.error("Error in rotation scheduler: %s", e, exc_info=True)

    async def _rotate_due_devices(self) -> None:
        """Find and rotate images on devices past their scheduled time."""
        now = datetime.now()

        async with AsyncSession(self.engine) as session:
            # Find online devices due for rotation
            query = (
                select(DeviceDisplayState)
                .where(DeviceDisplayState.is_online == True)  # noqa: E712
                .where(DeviceDisplayState.scheduled_next_at <= now)
            )
            result = await session.exec(query)
            due_states = result.all()

        for state in due_states:
            await self._rotate_single_device(state.global_device_id)

    async def _rotate_single_device(self, global_device_id: UUID) -> None:
        """Rotate image on a single device.

        Args:
            global_device_id: UUID of the GlobalDevice to rotate

        """
        if self.image_manager is None:
            return

        # Find the GlobalDevice from cache
        device: GlobalDevice | None = None
        for d in self.global_devices:
            if d.id == global_device_id:
                device = d
                break

        if device is None:
            self.logger.warning("Device %s not found in cache for rotation", global_device_id)
            return

        # Get next image
        image = await self.image_manager.get_next_image_for_device(device)
        if image is None:
            self.logger.debug("No images available for device %s", device.name)
            return

        # Send display command (this updates scheduled_next_at)
        await self.image_manager.send_display_command(device, image)
        self.logger.info("Auto-rotated to image '%s' on %s", image.title or image.id, device.name)
