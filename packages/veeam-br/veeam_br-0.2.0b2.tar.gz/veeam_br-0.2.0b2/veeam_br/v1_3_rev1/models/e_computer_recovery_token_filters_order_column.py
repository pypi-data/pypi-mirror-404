from enum import Enum


class EComputerRecoveryTokenFiltersOrderColumn(str, Enum):
    EXPIRATIONDATE = "ExpirationDate"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
