from enum import Enum


class EntraIdTenantItemRecursiveComparisonSessionModelStatus(str, Enum):
    FAILURE = "Failure"
    RUNNING = "Running"
    SUCCESS = "Success"

    def __str__(self) -> str:
        return str(self.value)
