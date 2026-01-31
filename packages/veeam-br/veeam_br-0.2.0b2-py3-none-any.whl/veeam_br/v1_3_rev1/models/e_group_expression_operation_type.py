from enum import Enum


class EGroupExpressionOperationType(str, Enum):
    AND = "And"
    NOT = "Not"
    OR = "Or"

    def __str__(self) -> str:
        return str(self.value)
