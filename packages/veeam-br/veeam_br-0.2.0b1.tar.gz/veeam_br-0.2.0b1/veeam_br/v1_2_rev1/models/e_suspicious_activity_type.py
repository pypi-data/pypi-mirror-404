from enum import Enum


class ESuspiciousActivityType(str, Enum):
    ANTIVIRUSSCAN = "AntivirusScan"
    DELETEDUSEFULFILES = "DeletedUsefulFiles"
    ENCRYPTEDDATA = "EncryptedData"
    INDICATOROFCOMPROMISE = "IndicatorOfCompromise"
    MALWAREEXTENSIONS = "MalwareExtensions"
    RANSOMWARENOTES = "RansomwareNotes"
    RENAMEDFILES = "RenamedFiles"
    UNKNOWN = "Unknown"
    YARASCAN = "YaraScan"

    def __str__(self) -> str:
        return str(self.value)
