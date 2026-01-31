from enum import Enum


class EProtectionGroupCloudAccountType(str, Enum):
    AWS = "AWS"
    AZURE = "Azure"

    def __str__(self) -> str:
        return str(self.value)
