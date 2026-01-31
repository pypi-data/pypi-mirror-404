from enum import Enum


class EAgentThrottlingTargetType(str, Enum):
    ALLHOSTS = "AllHosts"
    SERVERS = "Servers"
    WORKSTATIONS = "Workstations"

    def __str__(self) -> str:
        return str(self.value)
