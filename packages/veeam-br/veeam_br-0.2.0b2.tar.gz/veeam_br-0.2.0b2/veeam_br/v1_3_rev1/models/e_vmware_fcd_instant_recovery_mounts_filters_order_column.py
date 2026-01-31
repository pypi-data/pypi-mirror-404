from enum import Enum


class EVmwareFcdInstantRecoveryMountsFiltersOrderColumn(str, Enum):
    NAME = "Name"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
