from enum import Enum


class EProxyType(str, Enum):
    GENERALPURPOSEPROXY = "GeneralPurposeProxy"
    HVPROXY = "HvProxy"
    VIPROXY = "ViProxy"

    def __str__(self) -> str:
        return str(self.value)
