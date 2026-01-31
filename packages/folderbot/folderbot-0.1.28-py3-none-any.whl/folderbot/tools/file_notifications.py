"""File notification tool inputs."""

from pydantic import BaseModel


class EnableFileNotificationsInput(BaseModel):
    """Input for enabling file change notifications."""

    pass  # No input needed


class DisableFileNotificationsInput(BaseModel):
    """Input for disabling file change notifications."""

    pass  # No input needed


class GetFileNotificationStatusInput(BaseModel):
    """Input for getting file notification status."""

    pass  # No input needed
