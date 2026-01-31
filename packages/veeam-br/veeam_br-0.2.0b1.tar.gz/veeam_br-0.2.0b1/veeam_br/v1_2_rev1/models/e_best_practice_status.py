from enum import Enum


class EBestPracticeStatus(str, Enum):
    ANALYZING = "Analyzing"
    NONE = "None"
    OK = "OK"
    SUPPRESSED = "Suppressed"
    UNABLETOCHECK = "UnableToCheck"
    VIOLATION = "Violation"

    def __str__(self) -> str:
        return str(self.value)
