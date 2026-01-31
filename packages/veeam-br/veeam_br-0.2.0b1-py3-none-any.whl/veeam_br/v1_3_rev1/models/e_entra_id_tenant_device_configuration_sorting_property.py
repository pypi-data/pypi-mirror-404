from enum import Enum


class EEntraIdTenantDeviceConfigurationSortingProperty(str, Enum):
    DESCRIPTION = "Description"
    DISPLAYNAME = "DisplayName"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"
    TYPE = "Type"
    VERSION = "Version"

    def __str__(self) -> str:
        return str(self.value)
