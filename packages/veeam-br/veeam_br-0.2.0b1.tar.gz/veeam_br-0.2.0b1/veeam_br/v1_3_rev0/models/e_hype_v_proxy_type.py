from enum import Enum


class EHypeVProxyType(str, Enum):
    OFFHOST = "offHost"
    ONHOST = "onHost"

    def __str__(self) -> str:
        return str(self.value)
