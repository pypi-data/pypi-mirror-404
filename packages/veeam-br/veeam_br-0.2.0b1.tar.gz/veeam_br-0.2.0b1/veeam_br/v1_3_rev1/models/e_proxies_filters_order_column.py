from enum import Enum


class EProxiesFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    HOSTNAME = "HostName"
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
