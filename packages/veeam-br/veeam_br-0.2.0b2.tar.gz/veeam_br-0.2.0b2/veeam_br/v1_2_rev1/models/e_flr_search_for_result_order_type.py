from enum import Enum


class EFlrSearchForResultOrderType(str, Enum):
    COMPARESTATE = "CompareState"
    CREATIONTIME = "CreationTime"
    EXTENSION = "Extension"
    MODIFICATIONTIME = "ModificationTime"
    NAME = "Name"
    OWNER = "Owner"
    PATH = "Path"
    SIZE = "Size"

    def __str__(self) -> str:
        return str(self.value)
