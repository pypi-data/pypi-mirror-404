from enum import Enum


class EReplicaRestorePointsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    NAME = "Name"
    PLATFORMID = "PlatformId"
    REPLICAID = "ReplicaId"

    def __str__(self) -> str:
        return str(self.value)
