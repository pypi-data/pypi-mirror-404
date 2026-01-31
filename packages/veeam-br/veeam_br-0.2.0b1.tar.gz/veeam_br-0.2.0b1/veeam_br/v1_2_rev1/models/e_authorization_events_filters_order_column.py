from enum import Enum


class EAuthorizationEventsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    EXPIRATIONTIME = "ExpirationTime"
    NAME = "Name"
    PROCESSEDTIME = "ProcessedTime"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
