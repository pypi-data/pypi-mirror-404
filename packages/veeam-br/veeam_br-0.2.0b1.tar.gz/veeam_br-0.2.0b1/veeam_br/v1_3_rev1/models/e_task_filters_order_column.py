from enum import Enum


class ETaskFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    ENDTIME = "EndTime"
    NAME = "Name"
    RESULT = "Result"
    STATE = "State"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
