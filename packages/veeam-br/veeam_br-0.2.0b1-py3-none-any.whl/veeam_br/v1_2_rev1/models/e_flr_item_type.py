from enum import Enum


class EFlrItemType(str, Enum):
    DRIVE = "Drive"
    FILE = "File"
    FOLDER = "Folder"
    LINK = "Link"

    def __str__(self) -> str:
        return str(self.value)
