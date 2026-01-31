from enum import Enum


class ESQLLogsProcessing(str, Enum):
    BACKUP = "Backup"
    NEVERTRUNCATE = "NeverTruncate"
    TRUNCATE = "Truncate"

    def __str__(self) -> str:
        return str(self.value)
