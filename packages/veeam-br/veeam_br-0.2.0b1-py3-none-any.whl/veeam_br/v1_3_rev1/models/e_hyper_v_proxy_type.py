from enum import Enum


class EHyperVProxyType(str, Enum):
    OFFHOST = "OffHost"
    ONHOST = "OnHost"

    def __str__(self) -> str:
        return str(self.value)
