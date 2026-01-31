from enum import Enum


class EAgentBackupTimeoutType(str, Enum):
    DAYS = "Days"
    HOURS = "Hours"
    MINUTES = "Minutes"

    def __str__(self) -> str:
        return str(self.value)
