from enum import Enum


class EVBRServerPlatform(str, Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
