from enum import Enum


class EEntraIdTenantRoleSortingProperty(str, Enum):
    DESCRIPTION = "Description"
    DISPLAYNAME = "DisplayName"
    ISBUILTIN = "IsBuiltIn"
    ISENABLED = "IsEnabled"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"

    def __str__(self) -> str:
        return str(self.value)
