from enum import Enum


class EHyperVHierarchyType(str, Enum):
    GROUPS = "Groups"
    HOSTSANDVMS = "HostsAndVms"
    HOSTSANDVOLUMES = "HostsAndVolumes"
    NETWORK = "Network"
    TAGS = "Tags"

    def __str__(self) -> str:
        return str(self.value)
