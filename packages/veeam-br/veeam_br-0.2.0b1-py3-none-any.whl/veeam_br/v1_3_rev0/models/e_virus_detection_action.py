from enum import Enum


class EVirusDetectionAction(str, Enum):
    ABORTRECOVERY = "AbortRecovery"
    DISABLENETWORK = "DisableNetwork"
    IGNORE = "Ignore"

    def __str__(self) -> str:
        return str(self.value)
