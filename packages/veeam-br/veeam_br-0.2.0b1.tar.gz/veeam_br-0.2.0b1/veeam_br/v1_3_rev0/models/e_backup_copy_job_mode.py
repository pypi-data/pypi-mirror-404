from enum import Enum


class EBackupCopyJobMode(str, Enum):
    IMMEDIATE = "Immediate"
    PERIODIC = "Periodic"

    def __str__(self) -> str:
        return str(self.value)
