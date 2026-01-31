from enum import Enum


class EVmwareDisksTypeToProcess(str, Enum):
    ALLDISKS = "AllDisks"
    SELECTEDDISKS = "SelectedDisks"
    SYSTEMONLY = "SystemOnly"

    def __str__(self) -> str:
        return str(self.value)
