from enum import Enum


class EManagedServersFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"
    STATUS = "Status"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
