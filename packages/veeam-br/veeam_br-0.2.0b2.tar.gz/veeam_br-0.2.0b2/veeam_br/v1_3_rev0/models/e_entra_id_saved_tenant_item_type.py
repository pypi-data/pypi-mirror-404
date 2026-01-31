from enum import Enum


class EEntraIdSavedTenantItemType(str, Enum):
    ADMINISTRATIVEUNIT = "AdministrativeUnit"
    APPLICATION = "Application"
    ARMROLEASSIGNMENT = "ArmRoleAssignment"
    CONDITIONALACCESSPOLICY = "ConditionalAccessPolicy"
    GROUP = "Group"
    SCHEMAEXTENSION = "SchemaExtension"
    SERVICEPRINCIPAL = "ServicePrincipal"
    UNIFIEDROLEASSIGNMENT = "UnifiedRoleAssignment"
    UNIFIEDROLEASSIGNMENTSCHEDULE = "UnifiedRoleAssignmentSchedule"
    UNIFIEDROLEASSIGNMENTSCHEDULEINSTANCE = "UnifiedRoleAssignmentScheduleInstance"
    UNIFIEDROLEDEFINITION = "UnifiedRoleDefinition"
    UNIFIEDROLEELIGIBILITYSCHEDULE = "UnifiedRoleEligibilitySchedule"
    UNIFIEDROLEELIGIBILITYSCHEDULEINSTANCE = "UnifiedRoleEligibilityScheduleInstance"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
