from enum import Enum


class ERepositoryAccessType(str, Enum):
    ALLOWALL = "AllowAll"
    ALLOWEXPLICIT = "AllowExplicit"
    DENYALL = "DenyAll"

    def __str__(self) -> str:
        return str(self.value)
