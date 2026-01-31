from enum import Enum


class EUnstructuredDataInstantRestoreOverwriteMode(str, Enum):
    OVERWRITE = "Overwrite"
    REPLACEOLDER = "ReplaceOlder"

    def __str__(self) -> str:
        return str(self.value)
