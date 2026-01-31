from enum import Enum


class EInventoryPlatformType(str, Enum):
    AGENT = "Agent"
    CLOUDDIRECTOR = "CloudDirector"
    HYPERV = "HyperV"
    VSPHERE = "VSphere"

    def __str__(self) -> str:
        return str(self.value)
