from enum import Enum


class EPlacementPolicyType(str, Enum):
    DATALOCALITY = "DataLocality"
    PERFORMANCE = "Performance"

    def __str__(self) -> str:
        return str(self.value)
