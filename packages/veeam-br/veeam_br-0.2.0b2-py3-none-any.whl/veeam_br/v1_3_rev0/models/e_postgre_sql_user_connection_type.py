from enum import Enum


class EPostgreSQLUserConnectionType(str, Enum):
    CREDENTIALS = "credentials"
    PASSWORDFILE = "passwordFile"
    PEER = "peer"

    def __str__(self) -> str:
        return str(self.value)
