from enum import Enum


class EACLHandlingBackupMode(str, Enum):
    FILESANDFOLDERS = "FilesAndFolders"
    FOLDERSONLY = "FoldersOnly"

    def __str__(self) -> str:
        return str(self.value)
