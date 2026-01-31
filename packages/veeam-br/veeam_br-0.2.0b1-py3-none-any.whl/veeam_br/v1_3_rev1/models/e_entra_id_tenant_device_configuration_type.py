from enum import Enum


class EEntraIdTenantDeviceConfigurationType(str, Enum):
    DEVICECOMPLIANCEPOLICY = "DeviceCompliancePolicy"
    DEVICECONFIGURATIONPOLICY = "DeviceConfigurationPolicy"

    def __str__(self) -> str:
        return str(self.value)
