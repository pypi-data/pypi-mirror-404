from enum import Enum


class EFlrBrowseMountFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"

    def __str__(self) -> str:
        return str(self.value)
