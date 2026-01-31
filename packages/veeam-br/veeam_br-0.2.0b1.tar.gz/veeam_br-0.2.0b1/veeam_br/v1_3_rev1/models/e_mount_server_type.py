from enum import Enum


class EMountServerType(str, Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
