from enum import Enum


class EEntraIdTenantRestorePointSortingProperty(str, Enum):
    CREATIONTIME = "creationTime"

    def __str__(self) -> str:
        return str(self.value)
