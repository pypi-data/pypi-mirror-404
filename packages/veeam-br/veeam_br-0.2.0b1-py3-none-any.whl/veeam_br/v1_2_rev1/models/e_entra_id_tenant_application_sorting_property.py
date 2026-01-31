from enum import Enum


class EEntraIdTenantApplicationSortingProperty(str, Enum):
    APPLICATIONTYPE = "applicationType"
    DESCRIPTION = "description"
    DISPLAYNAME = "displayName"
    ENABLED = "enabled"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"
    TAGS = "tags"

    def __str__(self) -> str:
        return str(self.value)
