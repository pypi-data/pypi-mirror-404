from enum import Enum


class EBackupItemVersionRetentionType(str, Enum):
    ARCHIVE = "Archive"
    BACKUPANDARCHIVE = "BackupAndArchive"
    NONE = "None"

    def __str__(self) -> str:
        return str(self.value)
