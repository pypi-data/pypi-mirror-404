from enum import Enum


class EPowerOffAction(str, Enum):
    BACKUPATPOWERON = "BackupAtPowerOn"
    SKIPBACKUP = "SkipBackup"

    def __str__(self) -> str:
        return str(self.value)
