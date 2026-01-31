from enum import Enum


class ETaskLogRecordStatus(str, Enum):
    FAILED = "Failed"
    NONE = "None"
    SUCCEEDED = "Succeeded"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
