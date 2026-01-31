from enum import Enum


class EBackupsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    JOBID = "JobId"
    NAME = "Name"
    PLATFORMID = "PlatformId"
    POLICYTAG = "PolicyTag"

    def __str__(self) -> str:
        return str(self.value)
