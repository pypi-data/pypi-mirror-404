from enum import Enum


class EWANAcceleratorsFiltersOrderColumn(str, Enum):
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
