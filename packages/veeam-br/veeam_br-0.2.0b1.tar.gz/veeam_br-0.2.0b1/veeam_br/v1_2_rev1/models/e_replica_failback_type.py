from enum import Enum


class EReplicaFailbackType(str, Enum):
    CUSTOMIZED = "Customized"
    ORIGINALLOCATION = "OriginalLocation"
    ORIGINALVM = "OriginalVM"

    def __str__(self) -> str:
        return str(self.value)
