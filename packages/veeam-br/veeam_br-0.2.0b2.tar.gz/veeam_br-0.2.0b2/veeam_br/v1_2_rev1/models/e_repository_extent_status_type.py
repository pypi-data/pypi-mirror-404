from enum import Enum


class ERepositoryExtentStatusType(str, Enum):
    EVACUATE = "Evacuate"
    MAINTENANCE = "Maintenance"
    NORMAL = "Normal"
    PENDING = "Pending"
    RESYNCREQUIRED = "ResyncRequired"
    SEALED = "Sealed"
    TENANTEVACUATING = "TenantEvacuating"

    def __str__(self) -> str:
        return str(self.value)
