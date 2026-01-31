from enum import Enum


class ESmbV3HostType(str, Enum):
    SMBV3CLUSTER = "SmbV3Cluster"
    SMBV3STANDALONEHOST = "SmbV3StandaloneHost"

    def __str__(self) -> str:
        return str(self.value)
