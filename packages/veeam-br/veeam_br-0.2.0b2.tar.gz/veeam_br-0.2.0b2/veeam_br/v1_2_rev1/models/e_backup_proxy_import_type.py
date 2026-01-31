from enum import Enum


class EBackupProxyImportType(str, Enum):
    VMWARE = "vmware"

    def __str__(self) -> str:
        return str(self.value)
