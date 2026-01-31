from enum import Enum


class EFlrPlatformType(str, Enum):
    AGENT = "Agent"
    CLOUDDIRECTOR = "CloudDirector"
    HYPERV = "HyperV"
    VMWARE = "VMware"

    def __str__(self) -> str:
        return str(self.value)
