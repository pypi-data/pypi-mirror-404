from enum import Enum


class EEntireVMRestoreModeType(str, Enum):
    CUSTOMIZED = "Customized"
    ORIGINALLOCATION = "OriginalLocation"

    def __str__(self) -> str:
        return str(self.value)
