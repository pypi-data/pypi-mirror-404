from enum import Enum


class EEntraIDTenantItemCounterType(str, Enum):
    FAILED = "Failed"
    SUCCESSFUL = "Successful"

    def __str__(self) -> str:
        return str(self.value)
