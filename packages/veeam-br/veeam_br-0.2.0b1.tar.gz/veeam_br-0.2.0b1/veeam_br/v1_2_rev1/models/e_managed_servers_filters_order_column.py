from enum import Enum


class EManagedServersFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
