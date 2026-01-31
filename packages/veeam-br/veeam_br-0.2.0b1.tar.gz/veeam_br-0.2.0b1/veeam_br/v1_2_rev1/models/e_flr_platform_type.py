from enum import Enum


class EFlrPlatformType(str, Enum):
    AGENT = "Agent"
    HYPERV = "HyperV"
    VMWARE = "VMware"

    def __str__(self) -> str:
        return str(self.value)
