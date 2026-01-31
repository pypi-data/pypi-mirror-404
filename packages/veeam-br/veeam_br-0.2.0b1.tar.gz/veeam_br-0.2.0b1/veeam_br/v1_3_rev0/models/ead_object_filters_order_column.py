from enum import Enum


class EADObjectFiltersOrderColumn(str, Enum):
    FULLNAME = "FullName"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
