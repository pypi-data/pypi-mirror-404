from enum import Enum


class EFileBackupCopyJobScheduleType(str, Enum):
    CONTINUOUS = "Continuous"
    CUSTOM = "Custom"

    def __str__(self) -> str:
        return str(self.value)
