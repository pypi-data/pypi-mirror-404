from enum import Enum


class EEntraIdTenantRestorePointSortingProperty(str, Enum):
    CREATIONTIME = "CreationTime"

    def __str__(self) -> str:
        return str(self.value)
