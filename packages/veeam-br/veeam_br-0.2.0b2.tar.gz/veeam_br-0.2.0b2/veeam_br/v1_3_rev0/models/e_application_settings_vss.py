from enum import Enum


class EApplicationSettingsVSS(str, Enum):
    DISABLED = "disabled"
    IGNOREFAILURES = "ignoreFailures"
    REQUIRESUCCESS = "requireSuccess"

    def __str__(self) -> str:
        return str(self.value)
