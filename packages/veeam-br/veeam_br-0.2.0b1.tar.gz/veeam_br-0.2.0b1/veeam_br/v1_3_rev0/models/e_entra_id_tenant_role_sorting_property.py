from enum import Enum


class EEntraIdTenantRoleSortingProperty(str, Enum):
    DESCRIPTION = "description"
    DISPLAYNAME = "displayName"
    ISBUILTIN = "isBuiltIn"
    ISENABLED = "isEnabled"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"

    def __str__(self) -> str:
        return str(self.value)
