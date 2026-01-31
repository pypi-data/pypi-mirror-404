from enum import Enum


class EEntraIdTenantAdminUnitSortingProperty(str, Enum):
    DESCRIPTION = "Description"
    DISPLAYNAME = "DisplayName"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"
    VISIBILITY = "Visibility"

    def __str__(self) -> str:
        return str(self.value)
