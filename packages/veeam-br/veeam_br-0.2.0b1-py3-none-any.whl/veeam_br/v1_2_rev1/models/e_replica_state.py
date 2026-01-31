from enum import Enum


class EReplicaState(str, Enum):
    FAILBACK = "Failback"
    FAILEDFAILOVER = "FailedFailover"
    FAILOVER = "Failover"
    PERMANENTFAILOVER = "PermanentFailover"
    PROCESSING = "Processing"
    READY = "Ready"
    READYTOSWITCH = "ReadyToSwitch"
    SUREBACKUP = "SureBackup"

    def __str__(self) -> str:
        return str(self.value)
