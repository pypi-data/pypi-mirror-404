from enum import Enum


class EVmwareInventoryType(str, Enum):
    CATEGORY = "Category"
    CLUSTER = "Cluster"
    COMPUTERESOURCE = "ComputeResource"
    DATACENTER = "Datacenter"
    DATASTORE = "Datastore"
    DATASTORECLUSTER = "DatastoreCluster"
    DISK = "Disk"
    DVSNETWORK = "DVSNetwork"
    FOLDER = "Folder"
    HOST = "Host"
    MULTITAG = "Multitag"
    NETWORK = "Network"
    RESOURCEPOOL = "ResourcePool"
    SHAREDDISK = "SharedDisk"
    STORAGEPOLICY = "StoragePolicy"
    TAG = "Tag"
    TEMPLATE = "Template"
    UNKNOWN = "Unknown"
    VCENTERSERVER = "vCenterServer"
    VIRTUALAPP = "VirtualApp"
    VIRTUALMACHINE = "VirtualMachine"

    def __str__(self) -> str:
        return str(self.value)
