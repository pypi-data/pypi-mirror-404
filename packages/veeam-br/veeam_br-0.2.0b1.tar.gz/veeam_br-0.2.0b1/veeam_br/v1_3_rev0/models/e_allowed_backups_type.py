from enum import Enum


class EAllowedBackupsType(str, Enum):
    ALL = "All"
    FULLSONLY = "FullsOnly"
    INCREMENTSONLY = "IncrementsOnly"
    NONE = "None"

    def __str__(self) -> str:
        return str(self.value)
