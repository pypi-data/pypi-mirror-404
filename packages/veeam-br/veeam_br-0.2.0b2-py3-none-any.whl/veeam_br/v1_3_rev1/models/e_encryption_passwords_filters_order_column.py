from enum import Enum


class EEncryptionPasswordsFiltersOrderColumn(str, Enum):
    HINT = "Hint"
    MODIFICATIONTIME = "ModificationTime"

    def __str__(self) -> str:
        return str(self.value)
