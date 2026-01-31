from enum import Enum


class EAgentStatus(str, Enum):
    FAILED = "Failed"
    INSTALLED = "Installed"
    NOTINITIALIZED = "NotInitialized"
    NOTINSTALLED = "NotInstalled"
    UNKNOWN = "Unknown"
    UNSUPPORTEDOPERATINGSYSTEM = "UnsupportedOperatingSystem"
    UPGRADEREQUIRED = "UpgradeRequired"

    def __str__(self) -> str:
        return str(self.value)
