from enum import Enum


class EKMSCertificateType(str, Enum):
    CLIENT = "Client"
    SERVER = "Server"

    def __str__(self) -> str:
        return str(self.value)
