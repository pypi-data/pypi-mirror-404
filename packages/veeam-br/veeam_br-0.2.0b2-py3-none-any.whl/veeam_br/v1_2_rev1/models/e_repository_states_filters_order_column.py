from enum import Enum


class ERepositoryStatesFiltersOrderColumn(str, Enum):
    CAPACITYGB = "CapacityGB"
    DESCRIPTION = "Description"
    FREEGB = "FreeGB"
    HOST = "Host"
    NAME = "Name"
    PATH = "Path"
    TYPE = "Type"
    USEDSPACEGB = "UsedSpaceGB"

    def __str__(self) -> str:
        return str(self.value)
