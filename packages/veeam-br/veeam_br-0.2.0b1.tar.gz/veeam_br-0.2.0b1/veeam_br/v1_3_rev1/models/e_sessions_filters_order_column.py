from enum import Enum


class ESessionsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    ENDTIME = "EndTime"
    INITIATEDBY = "InitiatedBy"
    NAME = "Name"
    RESULT = "Result"
    SESSIONTYPE = "SessionType"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
