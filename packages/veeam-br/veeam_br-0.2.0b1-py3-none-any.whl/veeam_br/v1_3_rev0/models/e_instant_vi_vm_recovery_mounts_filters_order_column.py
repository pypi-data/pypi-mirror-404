from enum import Enum


class EInstantViVMRecoveryMountsFiltersOrderColumn(str, Enum):
    HOSTNAME = "hostName"
    JOBNAME = "jobName"
    RESTOREPOINTDATE = "restorePointDate"
    STATE = "state"
    VMNAME = "vmName"

    def __str__(self) -> str:
        return str(self.value)
