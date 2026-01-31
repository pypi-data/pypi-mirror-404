from enum import Enum


class EStorageOptimization(str, Enum):
    VALUE_0 = "256KB"
    VALUE_1 = "512KB"
    VALUE_2 = "1MB"
    VALUE_3 = "4MB"

    def __str__(self) -> str:
        return str(self.value)
