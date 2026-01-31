from enum import Enum


class EImmediateScheduleModel(str, Enum):
    BACKUPWINDOW = "BackupWindow"
    CONTINUOUS = "Continuous"

    def __str__(self) -> str:
        return str(self.value)
