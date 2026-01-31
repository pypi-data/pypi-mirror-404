from enum import Enum


class EBackupCopyRestorePoints(str, Enum):
    ALL = "All"
    LATEST = "Latest"

    def __str__(self) -> str:
        return str(self.value)
