from enum import Enum


class EBackupProxyTransportMode(str, Enum):
    AUTO = "auto"
    DIRECTACCESS = "directAccess"
    NETWORK = "network"
    VIRTUALAPPLIANCE = "virtualAppliance"

    def __str__(self) -> str:
        return str(self.value)
