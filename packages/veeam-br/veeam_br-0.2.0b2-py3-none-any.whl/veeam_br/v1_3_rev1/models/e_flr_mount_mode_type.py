from enum import Enum


class EFlrMountModeType(str, Enum):
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"

    def __str__(self) -> str:
        return str(self.value)
