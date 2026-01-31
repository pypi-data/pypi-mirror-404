from enum import Enum


class ETransactionLogsSettings(str, Enum):
    COPYONLY = "CopyOnly"
    PROCESS = "Process"

    def __str__(self) -> str:
        return str(self.value)
