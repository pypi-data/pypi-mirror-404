from enum import Enum


class EWindowsHostComponentType(str, Enum):
    AGENTCONFIGURESERVICE = "AgentConfigureService"
    CDP = "Cdp"
    CLOUDGATE = "CloudGate"
    CLOUDSERVICEINVOKER = "CloudServiceInvoker"
    CLOUDSERVICEREMOTING = "CloudServiceRemoting"
    DEPLOYERSVC = "DeployerSvc"
    EPAGENT = "EpAgent"
    EPAGENTSHAREDMANAGEMENTOBJECTS = "EpAgentSharedManagementObjects"
    EPAGENTSQLLOCALDB = "EpAgentSqlLocalDB"
    EPAGENTSQLSYSCLRTYPES = "EpAgentSqlSysClrTypes"
    FILESYSTEMVSSINTEGRATION = "FileSystemVssIntegration"
    GUESTCONTROL = "GuestControl"
    HVINTEGRATION = "HvIntegration"
    NFS = "Nfs"
    RESTOREPROXY = "RestoreProxy"
    TAPE = "Tape"
    TRANSPORT = "Transport"
    VALREDIST = "ValRedist"
    VAMREDIST = "VamRedist"
    VAWREDIST = "VawRedist"
    VSSHWSNAPSHOTPROVIDER = "VssHwSnapshotProvider"
    WANACCELERATOR = "WanAccelerator"

    def __str__(self) -> str:
        return str(self.value)
