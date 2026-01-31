from enum import Enum


class ECreatingSuspiciousActivitySeverity(str, Enum):
    INFECTED = "Infected"
    SUSPICIOUS = "Suspicious"

    def __str__(self) -> str:
        return str(self.value)
