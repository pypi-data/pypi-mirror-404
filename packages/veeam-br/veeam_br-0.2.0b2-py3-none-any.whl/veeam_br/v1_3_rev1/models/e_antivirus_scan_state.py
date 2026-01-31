from enum import Enum


class EAntivirusScanState(str, Enum):
    FINISHED = "Finished"
    INPROGRESS = "InProgress"
    NOTSTARTED = "NotStarted"

    def __str__(self) -> str:
        return str(self.value)
