from enum import Enum


class EWindowsVolumeType(str, Enum):
    CUSTOM = "Custom"
    OS = "OS"

    def __str__(self) -> str:
        return str(self.value)
