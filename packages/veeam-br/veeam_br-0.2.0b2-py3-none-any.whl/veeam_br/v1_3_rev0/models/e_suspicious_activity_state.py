from enum import Enum


class ESuspiciousActivityState(str, Enum):
    CREATED = "Created"
    FALSEPOSITIVE = "FalsePositive"

    def __str__(self) -> str:
        return str(self.value)
