from enum import Enum


class EHyperVInventoryType(str, Enum):
    CLUSTER = "Cluster"
    CLUSTERVOLUME = "ClusterVolume"
    CSV = "CSV"
    HOST = "Host"
    HOSTGROUP = "HostGroup"
    MANAGEMENTGROUP = "ManagementGroup"
    NETWORK = "Network"
    SCVMM = "Scvmm"
    TAG = "Tag"
    VIRTUALMACHINE = "VirtualMachine"
    VMGROUP = "VMGroup"
    VOLUME = "Volume"

    def __str__(self) -> str:
        return str(self.value)
