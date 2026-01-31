from enum import Enum


class EBackupContentMountsFiltersOrderColumn(str, Enum):
    STATE = "state"

    def __str__(self) -> str:
        return str(self.value)
