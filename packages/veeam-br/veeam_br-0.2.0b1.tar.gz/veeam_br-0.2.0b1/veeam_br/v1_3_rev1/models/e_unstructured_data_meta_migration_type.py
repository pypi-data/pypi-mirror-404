from enum import Enum


class EUnstructuredDataMetaMigrationType(str, Enum):
    CHECKEXISTENCE = "CheckExistence"
    COPYMETAFROMCACHE = "CopyMetaFromCache"
    DOWNLOADMETAFROMARCHIVE = "DownloadMetaFromArchive"

    def __str__(self) -> str:
        return str(self.value)
