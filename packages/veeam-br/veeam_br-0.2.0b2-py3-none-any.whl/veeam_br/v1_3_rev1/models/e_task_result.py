from enum import Enum


class ETaskResult(str, Enum):
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    NONE = "None"
    SUCCESS = "Success"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
