from enum import Enum


class EConfigBackupSMTPSettingsType(str, Enum):
    CUSTOM = "Custom"
    GLOBAL = "Global"

    def __str__(self) -> str:
        return str(self.value)
