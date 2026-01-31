from enum import Enum


class EJobType(str, Enum):
    BACKUPCOPY = "BackupCopy"
    CLOUDBACKUPAWS = "CloudBackupAWS"
    CLOUDBACKUPAZURE = "CloudBackupAzure"
    CLOUDBACKUPGOOGLE = "CloudBackupGoogle"
    CLOUDDIRECTORBACKUP = "CloudDirectorBackup"
    ENTRAIDAUDITLOGBACKUP = "EntraIDAuditLogBackup"
    ENTRAIDTENANTBACKUP = "EntraIDTenantBackup"
    ENTRAIDTENANTBACKUPCOPY = "EntraIDTenantBackupCopy"
    FILEBACKUP = "FileBackup"
    FILEBACKUPCOPY = "FileBackupCopy"
    HYPERVBACKUP = "HyperVBackup"
    LEGACYBACKUPCOPY = "LegacyBackupCopy"
    LINUXAGENTBACKUP = "LinuxAgentBackup"
    LINUXAGENTBACKUPSERVERPOLICY = "LinuxAgentBackupServerPolicy"
    LINUXAGENTBACKUPWORKSTATIONPOLICY = "LinuxAgentBackupWorkstationPolicy"
    OBJECTSTORAGEBACKUP = "ObjectStorageBackup"
    SUREBACKUPCONTENTSCAN = "SureBackupContentScan"
    UNKNOWN = "Unknown"
    VSPHEREBACKUP = "VSphereBackup"
    VSPHEREREPLICA = "VSphereReplica"
    WINDOWSAGENTBACKUP = "WindowsAgentBackup"
    WINDOWSAGENTBACKUPSERVERPOLICY = "WindowsAgentBackupServerPolicy"
    WINDOWSAGENTBACKUPWORKSTATIONPOLICY = "WindowsAgentBackupWorkstationPolicy"

    def __str__(self) -> str:
        return str(self.value)
