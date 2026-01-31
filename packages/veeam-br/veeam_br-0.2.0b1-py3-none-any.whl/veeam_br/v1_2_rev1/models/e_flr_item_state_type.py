from enum import Enum


class EFlrItemStateType(str, Enum):
    CHANGED = "Changed"
    COMPARING = "Comparing"
    DELETED = "Deleted"
    FAILEDTOCOMPARE = "FailedToCompare"
    NOTAVALIABLE = "NotAvaliable"
    UNCHANGED = "Unchanged"

    def __str__(self) -> str:
        return str(self.value)
