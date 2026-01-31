from enum import Enum


class EADDomainFiltersOrderColumn(str, Enum):
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
