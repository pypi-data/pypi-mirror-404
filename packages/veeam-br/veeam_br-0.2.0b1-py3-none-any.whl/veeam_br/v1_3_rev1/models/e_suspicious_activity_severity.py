from enum import Enum


class ESuspiciousActivitySeverity(str, Enum):
    CLEAN = "Clean"
    INFECTED = "Infected"
    INFORMATIVE = "Informative"
    SUSPICIOUS = "Suspicious"

    def __str__(self) -> str:
        return str(self.value)
