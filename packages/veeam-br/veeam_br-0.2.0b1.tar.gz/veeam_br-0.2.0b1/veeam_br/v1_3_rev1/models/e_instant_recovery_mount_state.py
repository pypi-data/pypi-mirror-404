from enum import Enum


class EInstantRecoveryMountState(str, Enum):
    DISMOUNTING = "Dismounting"
    FAILED = "Failed"
    MOUNTED = "Mounted"
    MOUNTING = "Mounting"

    def __str__(self) -> str:
        return str(self.value)
