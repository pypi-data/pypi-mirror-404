from enum import Enum


class EGroupExpressionOperationType(str, Enum):
    AND = "and"
    NOT = "not"
    OR = "or"

    def __str__(self) -> str:
        return str(self.value)
