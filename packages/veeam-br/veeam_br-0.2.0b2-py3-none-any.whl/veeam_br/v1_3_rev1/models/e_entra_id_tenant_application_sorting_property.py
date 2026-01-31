from enum import Enum


class EEntraIdTenantApplicationSortingProperty(str, Enum):
    APPLICATIONTYPE = "ApplicationType"
    DESCRIPTION = "Description"
    DISPLAYNAME = "DisplayName"
    ENABLED = "Enabled"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"
    TAGS = "Tags"

    def __str__(self) -> str:
        return str(self.value)
