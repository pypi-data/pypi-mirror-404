"""Authenticated MQTT client for device communication."""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aiomqtt

from private_assistant_picture_display_skill.config import DeviceMqttConfig
from private_assistant_picture_display_skill.models.commands import (
    DisplayCommand,
    RegistrationResponse,
)


class DeviceMqttClient:
    """Secondary MQTT client for authenticated device communication.

    This client connects to a separate Mosquitto broker with password
    authentication for secure communication with Inky display devices.

    Topics:
        Subscribe:
            - inky/register: Device registration requests
            - inky/+/status: Device status heartbeats

        Publish:
            - inky/{device_id}/command: Display commands
            - inky/{device_id}/registered: Registration confirmations
    """

    REGISTER_TOPIC = "inky/register"
    STATUS_TOPIC_PATTERN = "inky/+/status"
    COMMAND_TOPIC_TEMPLATE = "inky/{device_id}/command"
    REGISTERED_TOPIC_TEMPLATE = "inky/{device_id}/registered"
    _STATUS_TOPIC_PARTS = 3  # inky/{device_id}/status has 3 parts

    def __init__(self, config: DeviceMqttConfig, logger: logging.Logger) -> None:
        """Initialize the device MQTT client.

        Args:
            config: Device MQTT configuration with host, port, and credentials
            logger: Logger instance from parent skill

        """
        self.config = config
        self.logger = logger
        self._client: aiomqtt.Client | None = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator["DeviceMqttClient"]:
        """Connect to the device MQTT broker.

        Yields:
            Self for use in async context manager

        """
        async with aiomqtt.Client(
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
        ) as client:
            self._client = client
            self.logger.info(
                "Connected to device MQTT broker at %s:%d",
                self.config.host,
                self.config.port,
            )
            try:
                yield self
            finally:
                self._client = None
                self.logger.info("Disconnected from device MQTT broker")

    async def subscribe_device_topics(self) -> None:
        """Subscribe to device registration and status topics."""
        if self._client is None:
            raise RuntimeError("MQTT client not connected")

        await self._client.subscribe(self.REGISTER_TOPIC, qos=1)
        self.logger.info("Subscribed to device registration topic: %s", self.REGISTER_TOPIC)

        await self._client.subscribe(self.STATUS_TOPIC_PATTERN, qos=1)
        self.logger.info("Subscribed to device status topic: %s", self.STATUS_TOPIC_PATTERN)

    async def publish_command(self, device_id: str, command: DisplayCommand) -> None:
        """Publish a display command to a specific device.

        Args:
            device_id: Target device identifier
            command: Command to send

        """
        if self._client is None:
            raise RuntimeError("MQTT client not connected")

        topic = self.COMMAND_TOPIC_TEMPLATE.format(device_id=device_id)
        payload = command.model_dump_json()

        await self._client.publish(topic, payload, qos=1)
        self.logger.debug("Published command to %s: %s", topic, command.action)

    async def publish_registered(self, device_id: str, response: RegistrationResponse) -> None:
        """Send registration confirmation with MinIO credentials.

        Args:
            device_id: Device that registered
            response: Registration response with credentials

        """
        if self._client is None:
            raise RuntimeError("MQTT client not connected")

        topic = self.REGISTERED_TOPIC_TEMPLATE.format(device_id=device_id)
        payload = response.model_dump_json()

        await self._client.publish(topic, payload, qos=1)
        self.logger.info("Sent registration confirmation to %s", device_id)

    async def messages(self) -> AsyncIterator[aiomqtt.Message]:
        """Iterate over incoming MQTT messages.

        Yields:
            MQTT messages from subscribed topics

        """
        if self._client is None:
            raise RuntimeError("MQTT client not connected")

        async for message in self._client.messages:
            yield message

    @staticmethod
    def decode_payload(payload: bytes | bytearray | str | Any) -> dict[str, Any] | None:
        """Decode MQTT message payload to dictionary.

        Args:
            payload: Raw MQTT payload

        Returns:
            Decoded JSON dictionary or None if decoding fails

        """
        try:
            if isinstance(payload, bytes | bytearray):
                return json.loads(payload.decode("utf-8"))  # type: ignore[no-any-return]
            if isinstance(payload, str):
                return json.loads(payload)  # type: ignore[no-any-return]
            return None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def extract_device_id_from_topic(topic: str) -> str | None:
        """Extract device ID from a status topic.

        Args:
            topic: MQTT topic string (e.g., "inky/livingroom/status")

        Returns:
            Device ID or None if topic doesn't match expected pattern

        """
        parts = topic.split("/")
        if len(parts) == DeviceMqttClient._STATUS_TOPIC_PARTS and parts[0] == "inky" and parts[2] == "status":
            return parts[1]
        return None
