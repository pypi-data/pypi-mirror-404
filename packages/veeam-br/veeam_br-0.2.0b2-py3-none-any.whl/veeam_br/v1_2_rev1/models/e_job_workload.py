from enum import Enum


class EJobWorkload(str, Enum):
    APPLICATION = "application"
    CLOUDVM = "cloudVm"
    FILE = "file"
    SERVER = "server"
    VM = "vm"
    WORKSTATION = "workstation"

    def __str__(self) -> str:
        return str(self.value)
