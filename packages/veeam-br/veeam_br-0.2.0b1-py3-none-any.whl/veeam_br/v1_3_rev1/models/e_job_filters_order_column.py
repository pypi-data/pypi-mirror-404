from enum import Enum


class EJobFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
