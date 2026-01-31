from enum import Enum


class EManagedServerState(str, Enum):
    ANY = "Any"
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"

    def __str__(self) -> str:
        return str(self.value)
