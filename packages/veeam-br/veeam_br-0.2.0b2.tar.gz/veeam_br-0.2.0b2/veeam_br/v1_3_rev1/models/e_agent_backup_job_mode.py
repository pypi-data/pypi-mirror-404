from enum import Enum


class EAgentBackupJobMode(str, Enum):
    ENTIRECOMPUTER = "EntireComputer"
    FILELEVEL = "FileLevel"
    VOLUMES = "Volumes"

    def __str__(self) -> str:
        return str(self.value)
