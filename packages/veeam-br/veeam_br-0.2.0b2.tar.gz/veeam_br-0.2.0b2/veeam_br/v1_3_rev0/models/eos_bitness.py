from enum import Enum


class EOSBitness(str, Enum):
    UNKNOWN = "Unknown"
    X64 = "x64"
    X86 = "x86"

    def __str__(self) -> str:
        return str(self.value)
