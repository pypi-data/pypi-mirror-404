from enum import Enum


class ERetentionPolicyType(str, Enum):
    DAYS = "Days"
    RESTOREPOINTS = "RestorePoints"

    def __str__(self) -> str:
        return str(self.value)
