from enum import Enum


class EProtectionGroupType(str, Enum):
    ADOBJECTS = "ADObjects"
    CSVFILE = "CSVFile"
    INDIVIDUALCOMPUTERS = "IndividualComputers"
    MANUALLYADDED = "ManuallyAdded"
    MONGODB = "MongoDB"
    PREINSTALLEDAGENTS = "PreInstalledAgents"

    def __str__(self) -> str:
        return str(self.value)
