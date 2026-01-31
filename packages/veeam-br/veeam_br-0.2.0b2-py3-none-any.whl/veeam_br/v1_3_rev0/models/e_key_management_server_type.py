from enum import Enum


class EKeyManagementServerType(str, Enum):
    KMS = "KMS"

    def __str__(self) -> str:
        return str(self.value)
