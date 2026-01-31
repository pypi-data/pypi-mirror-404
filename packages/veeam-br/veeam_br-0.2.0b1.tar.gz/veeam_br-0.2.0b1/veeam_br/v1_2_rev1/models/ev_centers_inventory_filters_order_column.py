from enum import Enum


class EvCentersInventoryFiltersOrderColumn(str, Enum):
    NAME = "Name"
    OBJECTID = "ObjectId"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
