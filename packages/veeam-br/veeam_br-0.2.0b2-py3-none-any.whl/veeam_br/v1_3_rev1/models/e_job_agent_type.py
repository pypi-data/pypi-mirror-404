from enum import Enum


class EJobAgentType(str, Enum):
    FAILOVERCLUSTER = "FailoverCluster"
    SERVER = "Server"
    WORKSTATION = "Workstation"

    def __str__(self) -> str:
        return str(self.value)
