from enum import Enum


class ECredentialsType(str, Enum):
    LINUX = "Linux"
    MANAGEDSERVICE = "ManagedService"
    STANDARD = "Standard"

    def __str__(self) -> str:
        return str(self.value)
