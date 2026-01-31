from enum import Enum


class ERotatedDriveCleanupMode(str, Enum):
    CLEARBACKUPFOLDER = "ClearBackupFolder"
    CLEARREPOSITORYFOLDER = "ClearRepositoryFolder"
    DISABLED = "Disabled"

    def __str__(self) -> str:
        return str(self.value)
