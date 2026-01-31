from enum import Enum


class EAntivirusScanResult(str, Enum):
    CANCELED = "Canceled"
    CLEAN = "Clean"
    FAILED = "Failed"
    INCONCLUSIVE = "Inconclusive"
    INFECTED = "Infected"
    NONE = "None"

    def __str__(self) -> str:
        return str(self.value)
