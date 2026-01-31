from enum import Enum


class EUserType(str, Enum):
    EXTERNALGROUP = "ExternalGroup"
    EXTERNALUSER = "ExternalUser"
    INTERNALGROUP = "InternalGroup"
    INTERNALUSER = "InternalUser"

    def __str__(self) -> str:
        return str(self.value)
