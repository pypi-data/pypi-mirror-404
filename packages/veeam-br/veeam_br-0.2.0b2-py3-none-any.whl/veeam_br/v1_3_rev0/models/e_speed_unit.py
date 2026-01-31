from enum import Enum


class ESpeedUnit(str, Enum):
    KBYTEPERSEC = "KbytePerSec"
    MBITPERSPEC = "MbitPerSpec"
    MBYTEPERSEC = "MbytePerSec"

    def __str__(self) -> str:
        return str(self.value)
