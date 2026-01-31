from enum import Enum


class EEntraIdTenantRestoreDeviceCodeStatus(str, Enum):
    FAILURE = "Failure"
    PENDING = "Pending"
    SUCCESS = "Success"

    def __str__(self) -> str:
        return str(self.value)
