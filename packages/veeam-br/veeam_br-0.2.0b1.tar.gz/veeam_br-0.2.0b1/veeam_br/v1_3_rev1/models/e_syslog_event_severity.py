from enum import Enum


class ESyslogEventSeverity(str, Enum):
    ERROR = "Error"
    INFO = "Info"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
