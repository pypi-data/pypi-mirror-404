from enum import Enum


class EPlatformType(str, Enum):
    CLOUDDIRECTOR = "CloudDirector"
    CUSTOMPLATFORM = "CustomPlatform"
    ENTRAID = "EntraID"
    HYPERV = "HyperV"
    LINUXPHYSICAL = "LinuxPhysical"
    TAPE = "Tape"
    TEST = "Test"
    UNSTRUCTUREDDATA = "UnstructuredData"
    VMWARE = "VMware"
    WINDOWSPHYSICAL = "WindowsPhysical"

    def __str__(self) -> str:
        return str(self.value)
