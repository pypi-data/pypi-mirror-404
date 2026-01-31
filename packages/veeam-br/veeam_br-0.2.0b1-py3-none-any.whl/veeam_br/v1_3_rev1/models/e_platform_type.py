from enum import Enum


class EPlatformType(str, Enum):
    AWSEC2 = "AWSEC2"
    AZURECOMPUTE = "AzureCompute"
    CLOUDDIRECTOR = "CloudDirector"
    CUSTOMPLATFORM = "CustomPlatform"
    ENTRAID = "EntraID"
    GCE = "GCE"
    HYPERV = "HyperV"
    LINUXPHYSICAL = "LinuxPhysical"
    MONGODB = "MongoDb"
    TAPE = "Tape"
    TEST = "Test"
    UNSTRUCTUREDDATA = "UnstructuredData"
    VMWARE = "VMware"
    WINDOWSPHYSICAL = "WindowsPhysical"

    def __str__(self) -> str:
        return str(self.value)
