from enum import Enum


class ESQLLogsProcessing(str, Enum):
    BACKUP = "backup"
    NEVERTRUNCATE = "neverTruncate"
    TRUNCATE = "truncate"

    def __str__(self) -> str:
        return str(self.value)
