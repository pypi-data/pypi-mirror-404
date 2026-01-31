from enum import Enum


class EServicesFiltersOrderColumn(str, Enum):
    NAME = "Name"
    PORT = "Port"

    def __str__(self) -> str:
        return str(self.value)
