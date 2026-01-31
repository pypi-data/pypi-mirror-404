from enum import Enum


class ESocketWorkloadsFiltersOrderColumn(str, Enum):
    CORESNUMBER = "CoresNumber"
    HOSTID = "HostId"
    HOSTNAME = "HostName"
    NAME = "Name"
    SOCKETSNUMBER = "SocketsNumber"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
