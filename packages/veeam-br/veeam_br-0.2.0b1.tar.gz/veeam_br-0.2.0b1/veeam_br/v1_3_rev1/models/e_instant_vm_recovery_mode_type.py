from enum import Enum


class EInstantVMRecoveryModeType(str, Enum):
    CUSTOMIZED = "Customized"
    ORIGINALLOCATION = "OriginalLocation"

    def __str__(self) -> str:
        return str(self.value)
