from enum import Enum


class EMountServerSettingsType(str, Enum):
    BOTH = "Both"
    LINUX = "Linux"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
