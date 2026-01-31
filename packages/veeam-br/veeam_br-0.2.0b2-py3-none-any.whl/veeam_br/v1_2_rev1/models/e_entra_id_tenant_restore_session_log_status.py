from enum import Enum


class EEntraIdTenantRestoreSessionLogStatus(str, Enum):
    FAILED = "Failed"
    RUNNING = "Running"
    SUCCESS = "Success"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
