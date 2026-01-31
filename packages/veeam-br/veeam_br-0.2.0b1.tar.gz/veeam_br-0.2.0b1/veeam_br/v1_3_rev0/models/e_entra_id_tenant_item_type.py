from enum import Enum


class EEntraIdTenantItemType(str, Enum):
    ADMINUNIT = "AdminUnit"
    APPLICATION = "Application"
    BITLOCKERKEY = "BitlockerKey"
    CONDITIONALACCESSPOLICY = "ConditionalAccessPolicy"
    DEVICECOMPLIANCEPOLICY = "DeviceCompliancePolicy"
    DEVICECONFIGURATION = "DeviceConfiguration"
    GROUP = "Group"
    ROLE = "Role"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
