from enum import Enum


class ETaskState(str, Enum):
    STARTING = "Starting"
    STOPPED = "Stopped"
    STOPPING = "Stopping"
    WORKING = "Working"

    def __str__(self) -> str:
        return str(self.value)
