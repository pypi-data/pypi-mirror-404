from enum import Enum


class EBackupContentMountsFiltersOrderColumn(str, Enum):
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
