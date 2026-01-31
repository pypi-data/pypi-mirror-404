from enum import Enum


class EGuestOSType(str, Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
