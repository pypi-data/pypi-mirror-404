from enum import Enum


class ENFSShareServerProcessingMode(str, Enum):
    DIRECT = "Direct"
    STORAGESNAPSHOT = "StorageSnapshot"

    def __str__(self) -> str:
        return str(self.value)
