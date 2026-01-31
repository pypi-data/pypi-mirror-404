from enum import Enum


class EWANAcceleratorCacheSizeUnit(str, Enum):
    B = "B"
    GB = "GB"
    KB = "KB"
    MB = "MB"
    PB = "PB"
    TB = "TB"

    def __str__(self) -> str:
        return str(self.value)
