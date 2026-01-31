from enum import Enum


class ETaskSessionType(str, Enum):
    ANTIVIRUS = "Antivirus"
    BACKUP = "Backup"
    REPLICA = "Replica"
    RESTORE = "Restore"

    def __str__(self) -> str:
        return str(self.value)
