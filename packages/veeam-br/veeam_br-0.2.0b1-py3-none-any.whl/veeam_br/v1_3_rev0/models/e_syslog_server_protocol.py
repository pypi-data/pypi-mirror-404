from enum import Enum


class ESyslogServerProtocol(str, Enum):
    TCP = "Tcp"
    TLS = "Tls"
    UDP = "Udp"

    def __str__(self) -> str:
        return str(self.value)
