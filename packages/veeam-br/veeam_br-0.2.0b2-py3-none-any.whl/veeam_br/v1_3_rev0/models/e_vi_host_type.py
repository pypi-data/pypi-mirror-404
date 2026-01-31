from enum import Enum


class EViHostType(str, Enum):
    ESX = "ESX"
    ESXI = "ESXi"
    VC = "VC"

    def __str__(self) -> str:
        return str(self.value)
