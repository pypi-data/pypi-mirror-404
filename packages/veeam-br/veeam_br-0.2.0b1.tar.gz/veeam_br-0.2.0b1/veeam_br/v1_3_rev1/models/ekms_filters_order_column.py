from enum import Enum


class EKMSFiltersOrderColumn(str, Enum):
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
