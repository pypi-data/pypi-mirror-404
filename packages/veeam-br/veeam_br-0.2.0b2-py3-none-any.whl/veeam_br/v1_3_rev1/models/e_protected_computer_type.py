from enum import Enum


class EProtectedComputerType(str, Enum):
    LINUX = "Linux"

    def __str__(self) -> str:
        return str(self.value)
