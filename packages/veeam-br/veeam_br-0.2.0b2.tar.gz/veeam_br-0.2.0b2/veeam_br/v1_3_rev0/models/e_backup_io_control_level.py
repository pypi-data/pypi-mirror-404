from enum import Enum


class EBackupIOControlLevel(str, Enum):
    HIGH = "High"
    HIGHEST = "Highest"
    LOW = "Low"
    LOWEST = "Lowest"
    MEDIUM = "Medium"

    def __str__(self) -> str:
        return str(self.value)
