from enum import Enum


class ERolesFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
