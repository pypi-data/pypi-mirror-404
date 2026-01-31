from enum import Enum


class EObjectRestorePointsFiltersOrderColumn(str, Enum):
    BACKUPID = "BackupId"
    CREATIONTIME = "CreationTime"
    PLATFORMID = "PlatformId"

    def __str__(self) -> str:
        return str(self.value)
