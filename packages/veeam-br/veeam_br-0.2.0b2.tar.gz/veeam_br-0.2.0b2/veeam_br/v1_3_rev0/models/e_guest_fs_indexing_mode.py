from enum import Enum


class EGuestFSIndexingMode(str, Enum):
    DISABLE = "disable"
    INDEXALL = "indexAll"
    INDEXALLEXCEPT = "indexAllExcept"
    INDEXONLY = "indexOnly"

    def __str__(self) -> str:
        return str(self.value)
