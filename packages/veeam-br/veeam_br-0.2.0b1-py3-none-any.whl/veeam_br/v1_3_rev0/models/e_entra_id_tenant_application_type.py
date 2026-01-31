from enum import Enum


class EEntraIdTenantApplicationType(str, Enum):
    APPREGISTRATION = "AppRegistration"
    ENTERPRISEREGISTRATION = "EnterpriseRegistration"

    def __str__(self) -> str:
        return str(self.value)
