from enum import Enum


class EJobType(str, Enum):
    BACKUPCOPY = "BackupCopy"
    CLOUDDIRECTORBACKUP = "CloudDirectorBackup"
    ENTRAIDAUDITLOGBACKUP = "EntraIDAuditLogBackup"
    ENTRAIDTENANTBACKUP = "EntraIDTenantBackup"
    ENTRAIDTENANTBACKUPCOPY = "EntraIDTenantBackupCopy"
    FILEBACKUPCOPY = "FileBackupCopy"
    HYPERVBACKUP = "HyperVBackup"
    LEGACYBACKUPCOPY = "LegacyBackupCopy"
    LINUXAGENTBACKUP = "LinuxAgentBackup"
    UNKNOWN = "Unknown"
    VSPHEREBACKUP = "VSphereBackup"
    VSPHEREREPLICA = "VSphereReplica"
    WINDOWSAGENTBACKUP = "WindowsAgentBackup"

    def __str__(self) -> str:
        return str(self.value)
