from enum import Enum


class EAzureInstantRecoveryMountState(str, Enum):
    MIGRATING = "Migrating"
    READY = "Ready"
    READYTOSWITCH = "ReadyToSwitch"
    STARTING = "Starting"
    STOPPED = "Stopped"
    STOPPING = "Stopping"
    SWITCHING = "Switching"

    def __str__(self) -> str:
        return str(self.value)
