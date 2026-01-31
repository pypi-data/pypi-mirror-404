from enum import Enum


class EJobStatus(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    INACTIVE = "inactive"
    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"
    STOPPING = "stopping"

    def __str__(self) -> str:
        return str(self.value)
