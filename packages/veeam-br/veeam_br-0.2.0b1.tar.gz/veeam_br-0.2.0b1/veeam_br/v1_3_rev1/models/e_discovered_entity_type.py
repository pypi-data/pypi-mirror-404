from enum import Enum


class EDiscoveredEntityType(str, Enum):
    ACTIVEDIRECTORY = "ActiveDirectory"
    CLUSTER = "Cluster"
    COMPUTER = "Computer"

    def __str__(self) -> str:
        return str(self.value)
