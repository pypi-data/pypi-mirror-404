from enum import Enum


class BottleneckSeverity(str, Enum):
    HARD = "hard"
    NONE = "none"
    SOFT = "soft"

    def __str__(self) -> str:
        return str(self.value)
