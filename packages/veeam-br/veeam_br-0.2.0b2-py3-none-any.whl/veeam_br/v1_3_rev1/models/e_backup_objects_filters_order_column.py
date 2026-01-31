from enum import Enum


class EBackupObjectsFiltersOrderColumn(str, Enum):
    NAME = "Name"
    OBJECTID = "ObjectId"
    PLATFORMID = "PlatformId"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
