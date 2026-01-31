from enum import Enum


class BottleneckSeverity(str, Enum):
    HARD = "Hard"
    NONE = "None"
    SOFT = "Soft"

    def __str__(self) -> str:
        return str(self.value)
