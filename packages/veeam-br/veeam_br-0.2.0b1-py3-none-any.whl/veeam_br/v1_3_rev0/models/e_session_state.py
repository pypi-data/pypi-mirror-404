from enum import Enum


class ESessionState(str, Enum):
    IDLE = "Idle"
    PAUSING = "Pausing"
    POSTPROCESSING = "Postprocessing"
    RESUMING = "Resuming"
    STARTING = "Starting"
    STOPPED = "Stopped"
    STOPPING = "Stopping"
    WAITINGREPOSITORY = "WaitingRepository"
    WAITINGSLOT = "WaitingSlot"
    WAITINGTAPE = "WaitingTape"
    WORKING = "Working"

    def __str__(self) -> str:
        return str(self.value)
