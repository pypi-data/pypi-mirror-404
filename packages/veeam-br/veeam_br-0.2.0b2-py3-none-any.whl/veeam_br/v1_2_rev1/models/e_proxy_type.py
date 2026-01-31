from enum import Enum


class EProxyType(str, Enum):
    VIPROXY = "ViProxy"

    def __str__(self) -> str:
        return str(self.value)
