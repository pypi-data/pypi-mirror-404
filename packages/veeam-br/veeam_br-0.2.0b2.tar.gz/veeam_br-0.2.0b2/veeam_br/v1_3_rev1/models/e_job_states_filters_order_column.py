from enum import Enum


class EJobStatesFiltersOrderColumn(str, Enum):
    AFTERJOBNAME = "AfterJobName"
    DESCRIPTION = "Description"
    LASTRESULT = "LastResult"
    LASTRUN = "LastRun"
    NAME = "Name"
    NEXTRUN = "NextRun"
    OBJECTSCOUNT = "ObjectsCount"
    REPOSITORYID = "RepositoryId"
    REPOSITORYNAME = "RepositoryName"
    STATUS = "Status"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
