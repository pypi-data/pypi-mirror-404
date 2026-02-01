"""Device display state model for Inky displays."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class DeviceDisplayState(SQLModel, table=True):
    """Current display state for a device.

    Tracks what image is currently displayed, online status, and scheduling
    information for automatic image rotation. Links to GlobalDevice from
    commons via global_device_id.

    Attributes:
        global_device_id: Foreign key to global_devices.id
        is_online: Whether device is currently reachable
        current_image_id: Currently displayed image (nullable)
        displayed_since: When current image was displayed
        scheduled_next_at: When to show next image

    """

    __tablename__ = "device_display_states"

    global_device_id: UUID = Field(primary_key=True, foreign_key="global_devices.id")
    is_online: bool = Field(default=True, description="Whether device is currently reachable")
    current_image_id: UUID | None = Field(default=None, foreign_key="images.id")
    displayed_since: datetime | None = Field(default=None, description="When current image was displayed")
    scheduled_next_at: datetime = Field(default_factory=datetime.now, description="Scheduled time for next image")
