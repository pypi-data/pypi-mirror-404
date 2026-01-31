from enum import Enum


class EHierarchyType(str, Enum):
    DATASTORESANDVMS = "DatastoresAndVms"
    HOSTSANDCLUSTERS = "HostsAndClusters"
    HOSTSANDDATASTORES = "HostsAndDatastores"
    HOSTSANDDISKS = "HostsAndDisks"
    NETWORK = "Network"
    VMSANDTAGS = "VmsAndTags"
    VMSANDTEMPLATES = "VmsAndTemplates"
    VMWAREDATASTORES = "VmwareDatastores"

    def __str__(self) -> str:
        return str(self.value)
