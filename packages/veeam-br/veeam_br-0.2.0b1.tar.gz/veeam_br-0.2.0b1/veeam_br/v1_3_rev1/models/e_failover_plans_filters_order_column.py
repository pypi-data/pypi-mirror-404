from enum import Enum


class EFailoverPlansFiltersOrderColumn(str, Enum):
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
