from enum import Enum


class EEntraIdTenantResource(str, Enum):
    ADMINISTRATIVEUNITS = "AdministrativeUnits"
    APPLICATIONS = "Applications"
    CONDITIONALACCESSPOLICIES = "ConditionalAccessPolicies"
    GROUPS = "Groups"
    INTUNEPOLICIES = "IntunePolicies"
    LOGS = "Logs"
    ROLES = "Roles"
    USERS = "Users"

    def __str__(self) -> str:
        return str(self.value)
