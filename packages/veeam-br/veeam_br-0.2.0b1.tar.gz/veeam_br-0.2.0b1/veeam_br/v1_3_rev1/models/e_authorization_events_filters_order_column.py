from enum import Enum


class EAuthorizationEventsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    DESCRIPTION = "Description"
    EXPIRATIONTIME = "ExpirationTime"
    INITIATEDBY = "InitiatedBy"
    NAME = "Name"
    PROCESSEDBY = "ProcessedBy"
    PROCESSEDTIME = "ProcessedTime"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
