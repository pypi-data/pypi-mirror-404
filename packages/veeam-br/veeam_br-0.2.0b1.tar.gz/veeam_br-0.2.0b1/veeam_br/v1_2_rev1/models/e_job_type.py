from enum import Enum


class EJobType(str, Enum):
    BACKUP = "Backup"
    CLOUDDIRECTORBACKUP = "CloudDirectorBackup"
    ENTRAIDAUDITLOGBACKUP = "EntraIDAuditLogBackup"
    ENTRAIDTENANTBACKUP = "EntraIDTenantBackup"
    FILEBACKUPCOPY = "FileBackupCopy"
    VSPHEREREPLICA = "VSphereReplica"

    def __str__(self) -> str:
        return str(self.value)
