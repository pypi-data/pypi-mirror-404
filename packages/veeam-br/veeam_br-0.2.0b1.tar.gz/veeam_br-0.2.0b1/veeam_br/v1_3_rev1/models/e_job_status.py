from enum import Enum


class EJobStatus(str, Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"
    INACTIVE = "Inactive"
    RUNNING = "Running"
    STARTING = "Starting"
    STOPPED = "Stopped"
    STOPPING = "Stopping"

    def __str__(self) -> str:
        return str(self.value)
