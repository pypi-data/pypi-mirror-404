from enum import Enum


class EBackupProxyTransportMode(str, Enum):
    AUTO = "Auto"
    DIRECTACCESS = "DirectAccess"
    NETWORK = "Network"
    VIRTUALAPPLIANCE = "VirtualAppliance"

    def __str__(self) -> str:
        return str(self.value)
