from enum import Enum


class EBackupExclusionPolicy(str, Enum):
    DISABLED = "disabled"
    EXCLUDEONLY = "excludeOnly"
    INCLUDEONLY = "includeOnly"

    def __str__(self) -> str:
        return str(self.value)
