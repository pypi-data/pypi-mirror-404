from enum import Enum


class EEntraIDTenantItemChangeType(str, Enum):
    ADDED = "Added"
    DELETED = "Deleted"

    def __str__(self) -> str:
        return str(self.value)
