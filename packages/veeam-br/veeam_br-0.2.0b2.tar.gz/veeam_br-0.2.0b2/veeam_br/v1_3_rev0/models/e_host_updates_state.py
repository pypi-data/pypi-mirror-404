from enum import Enum


class EHostUpdatesState(str, Enum):
    AVAILABLE = "Available"
    CHECKINPROGRESS = "CheckInProgress"
    CHECKUPDATESFAILED = "CheckUpdatesFailed"
    INSTALLING = "Installing"
    LASTINSTALLFAILED = "LastInstallFailed"
    NOTAVAILABLE = "NotAvailable"
    OUTOFDATE = "OutOfDate"

    def __str__(self) -> str:
        return str(self.value)
