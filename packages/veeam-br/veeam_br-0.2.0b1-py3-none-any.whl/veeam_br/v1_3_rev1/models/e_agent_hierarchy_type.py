from enum import Enum


class EAgentHierarchyType(str, Enum):
    CLUSTERS = "Clusters"
    COMPUTERS = "Computers"

    def __str__(self) -> str:
        return str(self.value)
