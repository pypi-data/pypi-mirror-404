from enum import Enum


class ETaskType(str, Enum):
    COMMON = "Common"
    FLRDOWNLOAD = "FlrDownload"
    FLRRESTORE = "FlrRestore"
    FLRSEARCH = "FlrSearch"
    HIERARCHYRESCAN = "HierarchyRescan"

    def __str__(self) -> str:
        return str(self.value)
