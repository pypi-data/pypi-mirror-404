from enum import Enum


class EOperatingSystemPlatform(str, Enum):
    UNKNOWN = "Unknown"
    X64 = "X64"
    X86 = "X86"

    def __str__(self) -> str:
        return str(self.value)
