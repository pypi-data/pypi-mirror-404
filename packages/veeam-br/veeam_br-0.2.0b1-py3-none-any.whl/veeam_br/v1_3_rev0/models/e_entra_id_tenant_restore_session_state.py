from enum import Enum


class EEntraIdTenantRestoreSessionState(str, Enum):
    CANCELED = "Canceled"
    FAILED = "Failed"
    NEVEREXECUTED = "NeverExecuted"
    PENDING = "Pending"
    RUNNING = "Running"
    STOPPING = "Stopping"
    SUCCESS = "Success"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
