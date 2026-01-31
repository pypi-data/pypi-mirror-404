from enum import Enum


class EEntraIdTenantGroupMembershipType(str, Enum):
    ASSIGNED = "Assigned"
    DYNAMIC = "Dynamic"

    def __str__(self) -> str:
        return str(self.value)
