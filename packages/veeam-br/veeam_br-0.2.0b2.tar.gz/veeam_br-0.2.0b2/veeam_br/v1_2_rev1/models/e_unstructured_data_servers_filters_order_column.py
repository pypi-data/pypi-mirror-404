from enum import Enum


class EUnstructuredDataServersFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
