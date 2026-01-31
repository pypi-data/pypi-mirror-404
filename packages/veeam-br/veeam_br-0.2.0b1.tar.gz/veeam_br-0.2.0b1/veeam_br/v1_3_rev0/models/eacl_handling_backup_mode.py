from enum import Enum


class EACLHandlingBackupMode(str, Enum):
    FILESANDFOLDERS = "filesAndFolders"
    FOLDERSONLY = "foldersOnly"

    def __str__(self) -> str:
        return str(self.value)
