from enum import Enum


class EScaleOutRepositoryExtentType(str, Enum):
    ARCHIVE = "Archive"
    CAPACITY = "Capacity"
    PERFORMANCE = "Performance"

    def __str__(self) -> str:
        return str(self.value)
