from enum import Enum


class EJobWorkload(str, Enum):
    APPLICATION = "Application"
    CLOUDVM = "CloudVm"
    FILE = "File"
    SERVER = "Server"
    VM = "Vm"
    WORKSTATION = "Workstation"

    def __str__(self) -> str:
        return str(self.value)
