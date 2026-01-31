from enum import Enum


class EIndividualComputerConnectionType(str, Enum):
    CERTIFICATE = "Certificate"
    PERMANENTCREDENTIALS = "PermanentCredentials"
    SINGLEUSECREDENTIALS = "SingleUseCredentials"

    def __str__(self) -> str:
        return str(self.value)
