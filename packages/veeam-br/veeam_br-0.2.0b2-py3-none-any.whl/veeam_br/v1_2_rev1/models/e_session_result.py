from enum import Enum


class ESessionResult(str, Enum):
    FAILED = "Failed"
    NONE = "None"
    SUCCESS = "Success"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
