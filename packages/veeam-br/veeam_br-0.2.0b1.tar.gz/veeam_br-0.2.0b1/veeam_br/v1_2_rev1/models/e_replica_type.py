from enum import Enum


class EReplicaType(str, Enum):
    CDP = "CDP"
    REGULAR = "Regular"

    def __str__(self) -> str:
        return str(self.value)
