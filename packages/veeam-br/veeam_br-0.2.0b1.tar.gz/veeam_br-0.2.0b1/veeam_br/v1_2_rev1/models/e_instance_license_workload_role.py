from enum import Enum


class EInstanceLicenseWorkloadRole(str, Enum):
    SERVER = "Server"
    WORKSTATION = "Workstation"

    def __str__(self) -> str:
        return str(self.value)
