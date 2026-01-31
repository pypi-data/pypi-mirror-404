from enum import Enum


class EEntraIdTenantDeviceConfigurationSortingProperty(str, Enum):
    DESCRIPTION = "description"
    DISPLAYNAME = "displayName"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"
    VERSION = "version"

    def __str__(self) -> str:
        return str(self.value)
