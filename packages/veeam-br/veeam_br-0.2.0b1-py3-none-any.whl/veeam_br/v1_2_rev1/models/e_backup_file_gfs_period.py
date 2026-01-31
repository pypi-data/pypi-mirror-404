from enum import Enum


class EBackupFileGFSPeriod(str, Enum):
    MONTHLY = "Monthly"
    NONE = "None"
    QUARTERLY = "Quarterly"
    WEEKLY = "Weekly"
    YEARLY = "Yearly"

    def __str__(self) -> str:
        return str(self.value)
