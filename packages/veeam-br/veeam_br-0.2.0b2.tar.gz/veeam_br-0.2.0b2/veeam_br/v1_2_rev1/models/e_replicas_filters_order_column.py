from enum import Enum


class EReplicasFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    JOBID = "JobId"
    NAME = "Name"
    PLATFORMID = "PlatformId"
    POLICYTAG = "PolicyTag"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
