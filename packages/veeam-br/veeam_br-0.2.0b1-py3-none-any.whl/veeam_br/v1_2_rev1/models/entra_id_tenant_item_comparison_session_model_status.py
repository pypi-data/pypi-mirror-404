from enum import Enum


class EntraIdTenantItemComparisonSessionModelStatus(str, Enum):
    FAILURE = "Failure"
    RUNNING = "Running"
    SUCCESS = "Success"

    def __str__(self) -> str:
        return str(self.value)
