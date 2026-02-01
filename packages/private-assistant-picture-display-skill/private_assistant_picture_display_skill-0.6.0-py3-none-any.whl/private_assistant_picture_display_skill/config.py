"""Configuration for the Picture Display Skill."""

from private_assistant_commons import SkillConfig
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeviceMqttConfig(BaseSettings):
    """Configuration for the authenticated device MQTT broker.

    Loads from environment variables with DEVICE_MQTT_ prefix:
    - DEVICE_MQTT_HOST (default: localhost)
    - DEVICE_MQTT_PORT (default: 1883)
    - DEVICE_MQTT_USERNAME (required)
    - DEVICE_MQTT_PASSWORD (required)
    """

    model_config = SettingsConfigDict(env_prefix="DEVICE_MQTT_")

    host: str = Field(description="Device MQTT broker host")
    port: int = Field(description="Device MQTT broker port")
    username: str = Field(description="Device MQTT username for authentication")
    password: str = Field(description="Device MQTT password for authentication")


class MinioConfig(BaseSettings):
    """Configuration for MinIO image storage.

    Loads from environment variables with MINIO_ prefix:
    - MINIO_ENDPOINT (default: localhost:9000)
    - MINIO_BUCKET (default: inky-images)
    - MINIO_SECURE (default: false)
    - MINIO_READER_ACCESS_KEY (required)
    - MINIO_READER_SECRET_KEY (required)
    """

    model_config = SettingsConfigDict(env_prefix="MINIO_")

    endpoint: str = Field(description="MinIO server endpoint")
    bucket: str = Field(default="inky-images", description="Bucket for image storage")
    secure: bool = Field(default=False, description="Use HTTPS for MinIO connection")
    reader_access_key: str = Field(description="Access key for device read access")
    reader_secret_key: str = Field(description="Secret key for device read access")


class PictureSkillConfig(SkillConfig):
    """Extended configuration for Picture Display Skill.

    Inherits MQTT configuration from SkillConfig and adds:
    - Default display duration for images
    - Device timeout for online status tracking
    """

    default_display_duration: int = Field(
        default=3600,
        description="Default image display duration in seconds",
    )
    device_timeout_seconds: int = Field(
        default=120,
        description="Seconds without heartbeat before device marked offline",
    )
