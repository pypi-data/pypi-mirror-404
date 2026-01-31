from enum import Enum


class EInstantViVMRecoveryMountsFiltersOrderColumn(str, Enum):
    HOSTNAME = "HostName"
    JOBNAME = "JobName"
    RESTOREPOINTDATE = "RestorePointDate"
    STATE = "State"
    VMNAME = "VmName"

    def __str__(self) -> str:
        return str(self.value)
