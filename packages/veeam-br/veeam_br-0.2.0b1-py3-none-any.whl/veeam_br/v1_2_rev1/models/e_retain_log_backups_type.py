from enum import Enum


class ERetainLogBackupsType(str, Enum):
    KEEPONLYDAYS = "KeepOnlyDays"
    UNTILBACKUPDELETED = "untilBackupDeleted"

    def __str__(self) -> str:
        return str(self.value)
