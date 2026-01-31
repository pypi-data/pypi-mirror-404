from enum import Enum


class ERestorePointType(str, Enum):
    CDP = "Cdp"
    DIFFERENT = "Different"
    FULL = "Full"
    INCREMENT = "Increment"
    ROLLBACK = "Rollback"
    SNAPSHOT = "Snapshot"

    def __str__(self) -> str:
        return str(self.value)
