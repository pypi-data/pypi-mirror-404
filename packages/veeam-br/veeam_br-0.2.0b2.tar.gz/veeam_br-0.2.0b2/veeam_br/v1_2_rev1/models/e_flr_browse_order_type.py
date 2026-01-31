from enum import Enum


class EFlrBrowseOrderType(str, Enum):
    CREATIONDATE = "CreationDate"
    ITEMSTATE = "ItemState"
    MODIFIEDDATE = "ModifiedDate"
    NAME = "Name"
    SIZE = "Size"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
