from enum import Enum


class EEntraIdTenantBitlockerKeySortingProperty(str, Enum):
    DEVICEDISPLAYNAME = "DeviceDisplayName"
    DEVICEID = "DeviceId"
    KEY = "Key"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"

    def __str__(self) -> str:
        return str(self.value)
