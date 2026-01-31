from enum import Enum


class EInstantHvVMRecoveryMountsFiltersOrderColumn(str, Enum):
    HOSTNAME = "HostName"
    JOBNAME = "JobName"
    RESTOREPOINTDATE = "RestorePointDate"
    STATE = "State"
    VMNAME = "VmName"

    def __str__(self) -> str:
        return str(self.value)
