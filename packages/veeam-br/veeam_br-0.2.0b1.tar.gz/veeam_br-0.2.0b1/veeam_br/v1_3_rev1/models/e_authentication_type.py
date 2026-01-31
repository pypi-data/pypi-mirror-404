from enum import Enum


class EAuthenticationType(str, Enum):
    PASSWORD = "Password"
    SSHKEY = "SshKey"

    def __str__(self) -> str:
        return str(self.value)
