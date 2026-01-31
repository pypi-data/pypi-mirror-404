from enum import Enum


class EProtectionGroupType(str, Enum):
    ADOBJECTS = "ADObjects"
    CLOUDMACHINES = "CloudMachines"
    CSVFILE = "CSVFile"
    INDIVIDUALCOMPUTERS = "IndividualComputers"
    MANUALLYADDED = "ManuallyAdded"
    MONGODB = "MongoDB"
    PREINSTALLEDAGENTS = "PreInstalledAgents"
    UNMANAGED = "Unmanaged"

    def __str__(self) -> str:
        return str(self.value)
