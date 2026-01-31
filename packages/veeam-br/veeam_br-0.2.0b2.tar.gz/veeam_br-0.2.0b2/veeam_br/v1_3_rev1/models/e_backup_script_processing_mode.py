from enum import Enum


class EBackupScriptProcessingMode(str, Enum):
    DISABLEEXEC = "DisableExec"
    IGNOREEXECFAILURES = "IgnoreExecFailures"
    REQUIRESUCCESS = "RequireSuccess"

    def __str__(self) -> str:
        return str(self.value)
