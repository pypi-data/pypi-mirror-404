from enum import Enum


class EPredicateExpressionOperationType(str, Enum):
    CONTAINS = "contains"
    ENDSWITH = "endsWith"
    EQUALS = "equals"
    GREATERTHAN = "greaterThan"
    GREATERTHANOREQUAL = "greaterThanOrEqual"
    IN = "in"
    LESSTHAN = "lessThan"
    LESSTHANOREQUAL = "lessThanOrEqual"
    NOTEQUALS = "notEquals"
    STARTSWITH = "startsWith"

    def __str__(self) -> str:
        return str(self.value)
