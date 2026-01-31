from enum import Enum


class EEntraIdTenantAdminUnitVisibilityType(str, Enum):
    HIDDEN = "Hidden"
    PUBLIC = "Public"

    def __str__(self) -> str:
        return str(self.value)
