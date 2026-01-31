from enum import Enum


class ESuspiciousActivityEventsFiltersOrderColumn(str, Enum):
    BACKUPOBJECTID = "BackupObjectId"
    CREATEDBY = "CreatedBy"
    DETECTIONTIMEUTC = "DetectionTimeUtc"
    ENGINE = "Engine"
    SEVERITY = "Severity"
    SOURCE = "Source"
    STATE = "State"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
