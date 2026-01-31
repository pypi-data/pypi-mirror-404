from enum import Enum


class EEntraIdTenantItemType(str, Enum):
    ADMINUNIT = "AdminUnit"
    APPLICATION = "Application"
    CONDITIONALACCESSPOLICY = "ConditionalAccessPolicy"
    GROUP = "Group"
    ROLE = "Role"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
