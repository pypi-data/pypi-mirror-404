from enum import Enum


class EBackupFilesFiltersOrderColumn(str, Enum):
    BACKUPSIZE = "BackupSize"
    COMPRESSRATIO = "CompressRatio"
    CREATIONTIME = "CreationTime"
    DATASIZE = "DataSize"
    DEDUPRATIO = "DedupRatio"
    GFSPERIOD = "GFSPeriod"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
