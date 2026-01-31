from enum import Enum


class EEntraIDAuditLogRetentionPolicyType(str, Enum):
    DAYS = "Days"
    MONTHS = "Months"
    YEARS = "Years"

    def __str__(self) -> str:
        return str(self.value)
