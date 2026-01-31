from enum import Enum


class ECloudBrowserFolderType(str, Enum):
    ARCHIVE = "archive"
    BACKUP = "backup"

    def __str__(self) -> str:
        return str(self.value)
