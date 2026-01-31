from enum import Enum


class EPostgreSQLUserConnectionType(str, Enum):
    CREDENTIALS = "Credentials"
    PASSWORDFILE = "PasswordFile"
    PEER = "Peer"

    def __str__(self) -> str:
        return str(self.value)
