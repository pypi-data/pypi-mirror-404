from enum import Enum


class EGuestOSFamily(str, Enum):
    LINUX = "Linux"
    OTHER = "Other"
    UNKNOWN = "Unknown"
    WINDOWS = "Windows"

    def __str__(self) -> str:
        return str(self.value)
