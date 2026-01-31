from enum import Enum


class EFlrAuditItemsFiltersOrderColumn(str, Enum):
    INITIATORNAME = "InitiatorName"
    ITEMTYPE = "ItemType"
    JOBNAME = "JobName"
    NAME = "Name"
    RESTOREFINISHTIME = "RestoreFinishTime"
    RESTORESESSIONID = "RestoreSessionId"
    RESTORESTARTTIME = "RestoreStartTime"
    RESTORESTATUS = "RestoreStatus"
    SIZE = "Size"
    SOURCEPATH = "SourcePath"
    TARGETHOST = "TargetHost"
    TARGETPATH = "TargetPath"

    def __str__(self) -> str:
        return str(self.value)
