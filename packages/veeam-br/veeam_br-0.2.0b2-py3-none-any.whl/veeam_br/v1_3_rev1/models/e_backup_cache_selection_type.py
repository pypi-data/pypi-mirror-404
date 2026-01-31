from enum import Enum


class EBackupCacheSelectionType(str, Enum):
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"

    def __str__(self) -> str:
        return str(self.value)
