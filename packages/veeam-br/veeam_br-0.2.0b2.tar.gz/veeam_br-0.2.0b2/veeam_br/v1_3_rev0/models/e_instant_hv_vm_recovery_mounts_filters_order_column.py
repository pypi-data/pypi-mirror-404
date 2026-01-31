from enum import Enum


class EInstantHvVMRecoveryMountsFiltersOrderColumn(str, Enum):
    HOSTNAME = "hostName"
    JOBNAME = "jobName"
    RESTOREPOINTDATE = "restorePointDate"
    STATE = "state"
    VMNAME = "vmName"

    def __str__(self) -> str:
        return str(self.value)
