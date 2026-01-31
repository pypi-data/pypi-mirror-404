from enum import Enum


class EInstantUnstructuredDataRecoveryMountsFiltersOrderColumn(str, Enum):
    NAME = "Name"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
