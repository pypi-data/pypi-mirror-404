from enum import Enum


class ESharedFolderType(str, Enum):
    NFS = "NFS"
    SMB = "SMB"

    def __str__(self) -> str:
        return str(self.value)
