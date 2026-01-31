from enum import Enum


class ESennightOfMonth(str, Enum):
    FIFTH = "Fifth"
    FIRST = "First"
    FOURTH = "Fourth"
    LAST = "Last"
    SECOND = "Second"
    THIRD = "Third"

    def __str__(self) -> str:
        return str(self.value)
