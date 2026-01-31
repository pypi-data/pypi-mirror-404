from enum import Enum


class EMountServersFiltersOrderColumn(str, Enum):
    TYPE = "Type"
    WRITECACHEFOLDER = "WriteCacheFolder"

    def __str__(self) -> str:
        return str(self.value)
