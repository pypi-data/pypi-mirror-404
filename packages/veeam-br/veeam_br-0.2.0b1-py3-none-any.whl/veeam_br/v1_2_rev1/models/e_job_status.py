from enum import Enum


class EJobStatus(str, Enum):
    DISABLED = "disabled"
    INACTIVE = "inactive"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
