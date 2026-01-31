from enum import Enum


class EFlrBrowseOrderType(str, Enum):
    CREATIONDATE = "CreationDate"
    ITEMSTATE = "ItemState"
    LOCATION = "Location"
    MODIFIEDDATE = "ModifiedDate"
    NAME = "Name"
    OWNER = "Owner"
    SIZE = "Size"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
