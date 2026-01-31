from enum import Enum


class EEntraIdTenantConditionalAccessPolicyState(str, Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"
    ENABLEDFORREPORTINGBUTNOTENFORCED = "EnabledForReportingButNotEnforced"

    def __str__(self) -> str:
        return str(self.value)
