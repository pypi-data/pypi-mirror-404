from enum import Enum


class EProtectedComputerFiltersOrderColumn(str, Enum):
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
