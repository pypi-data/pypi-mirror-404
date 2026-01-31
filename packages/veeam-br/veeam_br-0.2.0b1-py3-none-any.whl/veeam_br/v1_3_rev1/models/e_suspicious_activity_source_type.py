from enum import Enum


class ESuspiciousActivitySourceType(str, Enum):
    EXTERNAL = "External"
    INTERNALVEEAMDETECTOR = "InternalVeeamDetector"
    MANUAL = "Manual"
    MARKASCLEANEVENT = "MarkAsCleanEvent"

    def __str__(self) -> str:
        return str(self.value)
