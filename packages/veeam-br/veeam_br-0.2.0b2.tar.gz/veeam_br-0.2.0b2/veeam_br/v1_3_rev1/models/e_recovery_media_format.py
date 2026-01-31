from enum import Enum


class ERecoveryMediaFormat(str, Enum):
    ISO = "Iso"

    def __str__(self) -> str:
        return str(self.value)
