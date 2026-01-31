from enum import Enum


class EBackupProxyImportType(str, Enum):
    VMWARE = "Vmware"

    def __str__(self) -> str:
        return str(self.value)
