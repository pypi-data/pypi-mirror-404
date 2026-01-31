from enum import Enum


class EHierarchyType(str, Enum):
    DATASTORESANDVMS = "DatastoresAndVms"
    HOSTSANDCLUSTERS = "HostsAndClusters"
    HOSTSANDDATASTORES = "HostsAndDatastores"
    NETWORK = "Network"
    VMSANDTAGS = "VmsAndTags"
    VMSANDTEMPLATES = "VmsAndTemplates"

    def __str__(self) -> str:
        return str(self.value)
