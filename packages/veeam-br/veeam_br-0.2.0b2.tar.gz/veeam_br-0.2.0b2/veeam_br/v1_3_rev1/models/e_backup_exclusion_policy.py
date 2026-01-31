from enum import Enum


class EBackupExclusionPolicy(str, Enum):
    DISABLED = "Disabled"
    EXCLUDEONLY = "ExcludeOnly"
    INCLUDEONLY = "IncludeOnly"

    def __str__(self) -> str:
        return str(self.value)
