from enum import Enum


class ESuspiciousActivityEventsFiltersOrderColumn(str, Enum):
    BACKUPOBJECTID = "BackupObjectId"
    CREATEDBY = "CreatedBy"
    CREATIONTIMEUTC = "CreationTimeUtc"
    DETAILS = "Details"
    DETECTIONTIMEUTC = "DetectionTimeUtc"
    ENGINE = "Engine"
    MACHINENAME = "MachineName"
    SEVERITY = "Severity"
    SOURCE = "Source"
    STATE = "State"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
