from enum import Enum


class EMountServerSettingsType(str, Enum):
    BOTH = "both"
    LINUX = "linux"
    WINDOWS = "windows"

    def __str__(self) -> str:
        return str(self.value)
