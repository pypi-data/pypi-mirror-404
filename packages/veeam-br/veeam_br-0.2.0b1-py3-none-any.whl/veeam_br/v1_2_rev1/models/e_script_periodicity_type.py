from enum import Enum


class EScriptPeriodicityType(str, Enum):
    BACKUPSESSIONS = "BackupSessions"
    DAYS = "Days"

    def __str__(self) -> str:
        return str(self.value)
