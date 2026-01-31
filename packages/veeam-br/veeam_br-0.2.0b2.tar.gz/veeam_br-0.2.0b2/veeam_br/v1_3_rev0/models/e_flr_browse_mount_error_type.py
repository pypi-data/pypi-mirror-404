from enum import Enum


class EFlrBrowseMountErrorType(str, Enum):
    FAILED = "Failed"
    SKIPPED = "Skipped"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
