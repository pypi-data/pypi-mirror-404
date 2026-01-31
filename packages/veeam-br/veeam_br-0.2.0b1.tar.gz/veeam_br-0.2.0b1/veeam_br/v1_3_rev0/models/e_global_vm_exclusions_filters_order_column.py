from enum import Enum


class EGlobalVMExclusionsFiltersOrderColumn(str, Enum):
    NAME = "Name"
    NOTE = "Note"

    def __str__(self) -> str:
        return str(self.value)
