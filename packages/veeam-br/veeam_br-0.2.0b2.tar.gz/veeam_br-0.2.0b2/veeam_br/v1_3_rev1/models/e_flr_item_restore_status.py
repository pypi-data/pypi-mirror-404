from enum import Enum


class EFlrItemRestoreStatus(str, Enum):
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    INPROGRESS = "InProgress"
    PENDING = "Pending"
    SKIPPED = "Skipped"
    SUCCEEDED = "Succeeded"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
