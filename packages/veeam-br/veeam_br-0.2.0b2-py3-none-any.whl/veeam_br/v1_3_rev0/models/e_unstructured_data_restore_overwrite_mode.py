from enum import Enum


class EUnstructuredDataRestoreOverwriteMode(str, Enum):
    OVERWRITE = "Overwrite"
    REPLACENEWER = "ReplaceNewer"
    REPLACEOLDER = "ReplaceOlder"
    SKIP = "Skip"

    def __str__(self) -> str:
        return str(self.value)
