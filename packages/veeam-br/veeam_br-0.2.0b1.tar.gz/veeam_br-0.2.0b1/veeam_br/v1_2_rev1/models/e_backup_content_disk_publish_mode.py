from enum import Enum


class EBackupContentDiskPublishMode(str, Enum):
    FUSE = "Fuse"
    ISCSI = "ISCSI"

    def __str__(self) -> str:
        return str(self.value)
