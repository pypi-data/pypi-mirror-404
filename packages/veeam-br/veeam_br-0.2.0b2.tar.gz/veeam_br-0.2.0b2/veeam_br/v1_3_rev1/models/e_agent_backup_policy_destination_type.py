from enum import Enum


class EAgentBackupPolicyDestinationType(str, Enum):
    BACKUPREPOSITORY = "BackupRepository"
    CLOUDCONNECTREPOSITORY = "CloudConnectRepository"
    LOCALSTORAGE = "LocalStorage"
    SHAREDFOLDER = "SharedFolder"

    def __str__(self) -> str:
        return str(self.value)
