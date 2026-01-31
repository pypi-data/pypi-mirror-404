from enum import Enum


class ETaskSessionsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    ENDTIME = "EndTime"
    NAME = "Name"
    RESULT = "Result"
    SCANRESULT = "ScanResult"
    SCANSTATE = "ScanState"
    SESSIONTYPE = "SessionType"
    STATE = "State"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
