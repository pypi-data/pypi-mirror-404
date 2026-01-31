from enum import Enum


class EManagedServersStatus(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"

    def __str__(self) -> str:
        return str(self.value)
