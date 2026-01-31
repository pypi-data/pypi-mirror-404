from enum import Enum


class EPredicateExpressionOperationType(str, Enum):
    CONTAINS = "Contains"
    ENDSWITH = "EndsWith"
    EQUALS = "Equals"
    GREATERTHAN = "GreaterThan"
    GREATERTHANOREQUAL = "GreaterThanOrEqual"
    IN = "In"
    LESSTHAN = "LessThan"
    LESSTHANOREQUAL = "LessThanOrEqual"
    NOTEQUALS = "NotEquals"
    STARTSWITH = "StartsWith"

    def __str__(self) -> str:
        return str(self.value)
