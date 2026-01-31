from enum import Enum


class EVmwareFcdInstantRecoveryMountsFiltersOrderColumn(str, Enum):
    NAME = "name"
    STATE = "state"

    def __str__(self) -> str:
        return str(self.value)
