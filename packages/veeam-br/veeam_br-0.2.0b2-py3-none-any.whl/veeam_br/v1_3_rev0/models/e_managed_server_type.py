from enum import Enum


class EManagedServerType(str, Enum):
    CLOUDDIRECTORHOST = "CloudDirectorHost"
    HVCLUSTER = "HvCluster"
    HVSERVER = "HvServer"
    LINUXHOST = "LinuxHost"
    SCVMM = "SCVMM"
    SMBV3CLUSTER = "SmbV3Cluster"
    SMBV3STANDALONEHOST = "SmbV3StandaloneHost"
    VIHOST = "ViHost"
    WINDOWSHOST = "WindowsHost"

    def __str__(self) -> str:
        return str(self.value)
