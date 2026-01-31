from enum import Enum


class ECertificateFileFormatType(str, Enum):
    PFX = "pfx"

    def __str__(self) -> str:
        return str(self.value)
