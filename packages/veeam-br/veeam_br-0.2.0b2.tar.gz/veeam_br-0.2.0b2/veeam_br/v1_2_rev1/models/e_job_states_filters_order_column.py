from enum import Enum


class EJobStatesFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    LASTRESULT = "LastResult"
    LASTRUN = "LastRun"
    NAME = "Name"
    NEXTRUN = "NextRun"
    OBJECTSCOUNT = "ObjectsCount"
    REPOSITORYID = "RepositoryId"
    STATUS = "Status"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
