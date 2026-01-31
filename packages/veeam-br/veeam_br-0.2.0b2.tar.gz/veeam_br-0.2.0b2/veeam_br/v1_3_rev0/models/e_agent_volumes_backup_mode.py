from enum import Enum


class EAgentVolumesBackupMode(str, Enum):
    ALLVOLUMESEXCEPT = "allVolumesExcept"
    SELECTEDVOLUMES = "selectedVolumes"

    def __str__(self) -> str:
        return str(self.value)
