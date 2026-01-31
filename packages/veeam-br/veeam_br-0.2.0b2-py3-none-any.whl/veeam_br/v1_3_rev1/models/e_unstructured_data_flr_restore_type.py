from enum import Enum


class EUnstructuredDataFLRRestoreType(str, Enum):
    CHANGEDONLY = "ChangedOnly"
    KEEP = "Keep"
    OVERWRITE = "Overwrite"

    def __str__(self) -> str:
        return str(self.value)
