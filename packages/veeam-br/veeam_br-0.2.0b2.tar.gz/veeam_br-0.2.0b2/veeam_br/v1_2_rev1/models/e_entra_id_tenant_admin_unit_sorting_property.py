from enum import Enum


class EEntraIdTenantAdminUnitSortingProperty(str, Enum):
    DESCRIPTION = "description"
    DISPLAYNAME = "displayName"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"
    VISIBILITY = "visibility"

    def __str__(self) -> str:
        return str(self.value)
