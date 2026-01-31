from enum import Enum


class EFailbackModeType(str, Enum):
    AUTO = "Auto"
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"

    def __str__(self) -> str:
        return str(self.value)
