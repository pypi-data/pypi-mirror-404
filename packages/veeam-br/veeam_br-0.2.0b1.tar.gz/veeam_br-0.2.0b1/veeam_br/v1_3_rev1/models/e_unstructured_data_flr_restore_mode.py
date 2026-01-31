from enum import Enum


class EUnstructuredDataFLRRestoreMode(str, Enum):
    CUSTOM = "Custom"
    LATESTPOINT = "LatestPoint"

    def __str__(self) -> str:
        return str(self.value)
