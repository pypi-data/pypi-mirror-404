from enum import Enum


class EFileBackupRetentionPolicyType(str, Enum):
    DAYS = "Days"
    MONTHS = "Months"

    def __str__(self) -> str:
        return str(self.value)
