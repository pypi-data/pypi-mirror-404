from enum import Enum


class EEntraIDTenantsFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
