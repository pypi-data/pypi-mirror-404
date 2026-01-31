from enum import Enum


class EInstalledLicenseStatus(str, Enum):
    EXPIRED = "Expired"
    INVALID = "Invalid"
    VALID = "Valid"

    def __str__(self) -> str:
        return str(self.value)
