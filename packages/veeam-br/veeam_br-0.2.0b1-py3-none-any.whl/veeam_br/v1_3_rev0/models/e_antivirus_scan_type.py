from enum import Enum


class EAntivirusScanType(str, Enum):
    ANTIVIRUS = "Antivirus"
    YARA = "Yara"

    def __str__(self) -> str:
        return str(self.value)
