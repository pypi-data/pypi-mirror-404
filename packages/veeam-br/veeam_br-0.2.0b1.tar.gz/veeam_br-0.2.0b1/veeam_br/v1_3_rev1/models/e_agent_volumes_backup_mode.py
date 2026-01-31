from enum import Enum


class EAgentVolumesBackupMode(str, Enum):
    ALLVOLUMESEXCEPT = "AllVolumesExcept"
    SELECTEDVOLUMES = "SelectedVolumes"

    def __str__(self) -> str:
        return str(self.value)
