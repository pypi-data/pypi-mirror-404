from enum import Enum


class EInstalledLicenseEdition(str, Enum):
    COMMUNITY = "Community"
    ENTERPRISE = "Enterprise"
    ENTERPRISEPLUS = "EnterprisePlus"
    STANDARD = "Standard"
    UNSPECIFIED = "Unspecified"

    def __str__(self) -> str:
        return str(self.value)
