from enum import Enum


class EBackupOracleLogsSettings(str, Enum):
    DELETEEXPIREDGBS = "DeleteExpiredGBs"
    DELETEEXPIREDHOURS = "DeleteExpiredHours"
    PRESERVE = "Preserve"

    def __str__(self) -> str:
        return str(self.value)
