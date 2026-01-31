from enum import Enum


class EApplicationSettingsVSS(str, Enum):
    DISABLED = "Disabled"
    IGNOREFAILURES = "IgnoreFailures"
    REQUIRESUCCESS = "RequireSuccess"

    def __str__(self) -> str:
        return str(self.value)
