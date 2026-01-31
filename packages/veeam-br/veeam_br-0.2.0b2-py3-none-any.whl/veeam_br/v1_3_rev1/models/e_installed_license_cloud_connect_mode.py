from enum import Enum


class EInstalledLicenseCloudConnectMode(str, Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"
    ENTERPRISE = "Enterprise"
    INVALID = "Invalid"

    def __str__(self) -> str:
        return str(self.value)
