from enum import Enum


class ECertificateFileFormatType(str, Enum):
    PEM = "pem"
    PFX = "pfx"

    def __str__(self) -> str:
        return str(self.value)
