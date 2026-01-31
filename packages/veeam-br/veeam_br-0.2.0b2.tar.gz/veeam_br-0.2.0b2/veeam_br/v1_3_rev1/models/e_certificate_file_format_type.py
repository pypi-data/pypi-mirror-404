from enum import Enum


class ECertificateFileFormatType(str, Enum):
    PEM = "Pem"
    PFX = "Pfx"

    def __str__(self) -> str:
        return str(self.value)
