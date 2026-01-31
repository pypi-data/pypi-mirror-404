from enum import Enum


class ECloudDirectorHierarchyType(str, Enum):
    DATASTORES = "Datastores"
    NETWORK = "Network"
    STORAGEPOLICIES = "StoragePolicies"
    VAPPSANDVMS = "VAppsAndVms"

    def __str__(self) -> str:
        return str(self.value)
