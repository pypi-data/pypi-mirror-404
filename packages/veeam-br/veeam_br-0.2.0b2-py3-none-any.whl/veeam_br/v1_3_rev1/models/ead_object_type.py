from enum import Enum


class EADObjectType(str, Enum):
    CLUSTER = "Cluster"
    COMPUTER = "Computer"
    CONTAINER = "Container"
    DOMAIN = "Domain"
    GROUP = "Group"
    ORGANIZATIONUNIT = "OrganizationUnit"

    def __str__(self) -> str:
        return str(self.value)
