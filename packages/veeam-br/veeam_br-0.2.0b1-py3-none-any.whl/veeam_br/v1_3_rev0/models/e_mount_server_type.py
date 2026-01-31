from enum import Enum


class EMountServerType(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"

    def __str__(self) -> str:
        return str(self.value)
