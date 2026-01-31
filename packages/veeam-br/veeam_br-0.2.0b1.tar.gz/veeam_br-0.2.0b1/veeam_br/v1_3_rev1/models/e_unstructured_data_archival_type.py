from enum import Enum


class EUnstructuredDataArchivalType(str, Enum):
    ALL = "All"
    EXCLUSIONMASK = "ExclusionMask"
    INCLUSIONMASK = "InclusionMask"

    def __str__(self) -> str:
        return str(self.value)
