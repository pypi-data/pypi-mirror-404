from enum import Enum


class ESMBShareServerProcessingMode(str, Enum):
    DIRECT = "Direct"
    STORAGESNAPSHOT = "StorageSnapshot"
    VSSSNAPSHOT = "VSSSnapshot"

    def __str__(self) -> str:
        return str(self.value)
