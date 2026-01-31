from enum import Enum


class ERepositoryConnectionType(str, Enum):
    DIRECT = "Direct"
    SELECTEDGATEWAY = "SelectedGateway"

    def __str__(self) -> str:
        return str(self.value)
