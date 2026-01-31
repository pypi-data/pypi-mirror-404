from enum import Enum


class ECredentialsStorageType(str, Enum):
    CERTIFICATE = "Certificate"
    PERMANENT = "Permanent"
    SINGLEUSE = "SingleUse"

    def __str__(self) -> str:
        return str(self.value)
