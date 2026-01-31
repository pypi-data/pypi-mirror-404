from enum import Enum


class ETaskSessionAlgorithm(str, Enum):
    FULL = "Full"
    INCREMENT = "Increment"
    NONE = "None"
    SYNTHETIC = "Synthetic"

    def __str__(self) -> str:
        return str(self.value)
