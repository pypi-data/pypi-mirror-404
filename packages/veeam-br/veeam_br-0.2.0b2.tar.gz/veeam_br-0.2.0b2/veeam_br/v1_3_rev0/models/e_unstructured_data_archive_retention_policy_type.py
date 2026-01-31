from enum import Enum


class EUnstructuredDataArchiveRetentionPolicyType(str, Enum):
    MONTHS = "Months"
    YEARS = "Years"

    def __str__(self) -> str:
        return str(self.value)
