from enum import Enum


class EConsumptionLimitKind(str, Enum):
    PB = "PB"
    TB = "TB"

    def __str__(self) -> str:
        return str(self.value)
