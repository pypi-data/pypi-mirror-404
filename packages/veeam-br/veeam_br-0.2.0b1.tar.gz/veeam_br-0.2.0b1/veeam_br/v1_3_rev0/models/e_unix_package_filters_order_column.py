from enum import Enum


class EUnixPackageFiltersOrderColumn(str, Enum):
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
