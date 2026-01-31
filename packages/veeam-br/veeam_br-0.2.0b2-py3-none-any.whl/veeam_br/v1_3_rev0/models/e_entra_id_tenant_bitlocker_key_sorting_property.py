from enum import Enum


class EEntraIdTenantBitlockerKeySortingProperty(str, Enum):
    DEVICEDISPLAYNAME = "deviceDisplayName"
    DEVICEID = "deviceId"
    KEY = "key"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"

    def __str__(self) -> str:
        return str(self.value)
