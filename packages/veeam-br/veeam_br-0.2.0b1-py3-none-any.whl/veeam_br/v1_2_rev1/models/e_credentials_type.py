from enum import Enum


class ECredentialsType(str, Enum):
    LINUX = "Linux"
    STANDARD = "Standard"

    def __str__(self) -> str:
        return str(self.value)
