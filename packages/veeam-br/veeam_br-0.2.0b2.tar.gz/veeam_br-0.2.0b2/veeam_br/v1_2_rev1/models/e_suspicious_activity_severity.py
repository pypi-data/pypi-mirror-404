from enum import Enum


class ESuspiciousActivitySeverity(str, Enum):
    CLEAN = "Clean"
    INFECTED = "Infected"
    SUSPICIOUS = "Suspicious"

    def __str__(self) -> str:
        return str(self.value)
