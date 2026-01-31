from enum import Enum


class EFlrType(str, Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
