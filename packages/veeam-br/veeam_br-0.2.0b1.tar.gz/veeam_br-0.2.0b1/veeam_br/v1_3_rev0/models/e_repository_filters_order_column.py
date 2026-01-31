from enum import Enum


class ERepositoryFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    HOST = "Host"
    NAME = "Name"
    PATH = "Path"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
