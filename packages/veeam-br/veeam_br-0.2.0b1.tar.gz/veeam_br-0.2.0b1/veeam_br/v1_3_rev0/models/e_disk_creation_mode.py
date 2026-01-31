from enum import Enum


class EDiskCreationMode(str, Enum):
    SOURCE = "Source"
    THICK = "Thick"
    THICKEAGERZEROED = "ThickEagerZeroed"
    THIN = "Thin"

    def __str__(self) -> str:
        return str(self.value)
