from enum import Enum


class EApplicationPluginStatus(str, Enum):
    INSTALLED = "Installed"
    NOTINSTALLED = "NotInstalled"
    UPGRADEREQUIRED = "UpgradeRequired"

    def __str__(self) -> str:
        return str(self.value)
