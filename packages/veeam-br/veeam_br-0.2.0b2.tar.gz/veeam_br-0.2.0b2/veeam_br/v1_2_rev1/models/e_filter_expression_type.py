from enum import Enum


class EFilterExpressionType(str, Enum):
    GROUPEXPRESSION = "GroupExpression"
    PREDICATEEXPRESSION = "PredicateExpression"

    def __str__(self) -> str:
        return str(self.value)
