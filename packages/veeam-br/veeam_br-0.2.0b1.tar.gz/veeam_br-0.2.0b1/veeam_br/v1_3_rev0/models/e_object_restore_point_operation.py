from enum import Enum


class EObjectRestorePointOperation(str, Enum):
    CHANGEREPLICAFAILBACKSWITCHOVERTIME = "ChangeReplicaFailbackSwitchoverTime"
    STARTENTIREVMRESTORE = "StartEntireVmRestore"
    STARTENTIREVMRESTORECLOUDDIRECTOR = "StartEntireVmRestoreCloudDirector"
    STARTENTIREVMRESTOREHYPERV = "StartEntireVmRestoreHyperV"
    STARTFCDINSTANTRECOVERY = "StartFCDInstantRecovery"
    STARTFLRRESTORE = "StartFlrRestore"
    STARTHVVMINSTANTRECOVERY = "StartHvVMInstantRecovery"
    STARTVIVMINSTANTRECOVERY = "StartViVMInstantRecovery"
    STARTVIVMSNAPSHOTREPLICACOMMITFAILBACK = "StartViVMSnapshotReplicaCommitFailback"
    STARTVIVMSNAPSHOTREPLICAFAILBACK = "StartViVMSnapshotReplicaFailback"
    STARTVIVMSNAPSHOTREPLICAFAILOVER = "StartViVMSnapshotReplicaFailover"
    STARTVIVMSNAPSHOTREPLICAPERMANENTFAILOVER = "StartViVMSnapshotReplicaPermanentFailover"
    STARTVIVMSNAPSHOTREPLICAPLANNEDFAILOVER = "StartViVMSnapshotReplicaPlannedFailover"
    STARTVIVMSNAPSHOTREPLICASWITCHTOPRODUCTIONFAILBACK = "StartViVMSnapshotReplicaSwitchToProductionFailback"
    STARTVIVMSNAPSHOTREPLICAUNDOFAILBACK = "StartViVMSnapshotReplicaUndoFailback"
    STARTVIVMSNAPSHOTREPLICAUNDOFAILOVER = "StartViVMSnapshotReplicaUndoFailover"

    def __str__(self) -> str:
        return str(self.value)
