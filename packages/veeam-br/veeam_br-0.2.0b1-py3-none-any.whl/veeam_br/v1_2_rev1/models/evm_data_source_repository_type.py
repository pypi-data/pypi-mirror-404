from enum import Enum


class EVMDataSourceRepositoryType(str, Enum):
    BACKUPFILES = "BackupFiles"
    PRODUCTIONSTORAGE = "ProductionStorage"

    def __str__(self) -> str:
        return str(self.value)
