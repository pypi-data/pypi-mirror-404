from enum import Enum


class ECloudBrowserFolderType(str, Enum):
    ARCHIVE = "Archive"
    BACKUP = "Backup"

    def __str__(self) -> str:
        return str(self.value)
