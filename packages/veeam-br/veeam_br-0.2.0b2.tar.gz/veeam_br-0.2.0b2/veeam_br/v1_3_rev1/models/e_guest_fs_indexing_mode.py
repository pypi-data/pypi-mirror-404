from enum import Enum


class EGuestFSIndexingMode(str, Enum):
    DISABLE = "Disable"
    INDEXALL = "IndexAll"
    INDEXALLEXCEPT = "IndexAllExcept"
    INDEXONLY = "IndexOnly"

    def __str__(self) -> str:
        return str(self.value)
