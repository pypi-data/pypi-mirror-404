from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TenantBackupObjectsSummaryResponse")


@_attrs_define
class TenantBackupObjectsSummaryResponse:
    """Summary of Microsoft Entra ID tenant backup objects.

    Attributes:
        azure_tenant_id (str): Tenant ID assigned by Microsoft Entra ID.
        users (int): Number of backed up users.
        administrative_units (int): Number of backed up administrative units.
        groups (int): Number of backed up groups.
        unified_role_definitions (int): Number of backed up unified role definitions.
        applications (int): Number of backed up applications.
        service_principals (int): Number of backed up service principals.
        arm_role_assignments (int): Number of backed up ARM role assignments.
        schema_extensions (int): Number of backed up schema extensions.
        unified_role_assignments (int): Number of backed up unified role assignments.
        unified_role_assignment_schedules (int): Number of backed up unified role assignment schedules.
        unified_role_assignment_schedule_instances (int): Number of backed up unified role assignment schedule
            instances.
        unified_role_eligibility_schedules (int): Number of backed up unified role eligibility schedules.
        unified_role_eligibility_schedule_instances (int): Number of backed up unified role eligibility schedule
            instances.
        conditional_access_policies (int): Number of backed up Conditional Access policies.
    """

    azure_tenant_id: str
    users: int
    administrative_units: int
    groups: int
    unified_role_definitions: int
    applications: int
    service_principals: int
    arm_role_assignments: int
    schema_extensions: int
    unified_role_assignments: int
    unified_role_assignment_schedules: int
    unified_role_assignment_schedule_instances: int
    unified_role_eligibility_schedules: int
    unified_role_eligibility_schedule_instances: int
    conditional_access_policies: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_tenant_id = self.azure_tenant_id

        users = self.users

        administrative_units = self.administrative_units

        groups = self.groups

        unified_role_definitions = self.unified_role_definitions

        applications = self.applications

        service_principals = self.service_principals

        arm_role_assignments = self.arm_role_assignments

        schema_extensions = self.schema_extensions

        unified_role_assignments = self.unified_role_assignments

        unified_role_assignment_schedules = self.unified_role_assignment_schedules

        unified_role_assignment_schedule_instances = self.unified_role_assignment_schedule_instances

        unified_role_eligibility_schedules = self.unified_role_eligibility_schedules

        unified_role_eligibility_schedule_instances = self.unified_role_eligibility_schedule_instances

        conditional_access_policies = self.conditional_access_policies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "azureTenantId": azure_tenant_id,
                "users": users,
                "administrativeUnits": administrative_units,
                "groups": groups,
                "unifiedRoleDefinitions": unified_role_definitions,
                "applications": applications,
                "servicePrincipals": service_principals,
                "armRoleAssignments": arm_role_assignments,
                "schemaExtensions": schema_extensions,
                "unifiedRoleAssignments": unified_role_assignments,
                "unifiedRoleAssignmentSchedules": unified_role_assignment_schedules,
                "unifiedRoleAssignmentScheduleInstances": unified_role_assignment_schedule_instances,
                "unifiedRoleEligibilitySchedules": unified_role_eligibility_schedules,
                "unifiedRoleEligibilityScheduleInstances": unified_role_eligibility_schedule_instances,
                "conditionalAccessPolicies": conditional_access_policies,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        azure_tenant_id = d.pop("azureTenantId")

        users = d.pop("users")

        administrative_units = d.pop("administrativeUnits")

        groups = d.pop("groups")

        unified_role_definitions = d.pop("unifiedRoleDefinitions")

        applications = d.pop("applications")

        service_principals = d.pop("servicePrincipals")

        arm_role_assignments = d.pop("armRoleAssignments")

        schema_extensions = d.pop("schemaExtensions")

        unified_role_assignments = d.pop("unifiedRoleAssignments")

        unified_role_assignment_schedules = d.pop("unifiedRoleAssignmentSchedules")

        unified_role_assignment_schedule_instances = d.pop("unifiedRoleAssignmentScheduleInstances")

        unified_role_eligibility_schedules = d.pop("unifiedRoleEligibilitySchedules")

        unified_role_eligibility_schedule_instances = d.pop("unifiedRoleEligibilityScheduleInstances")

        conditional_access_policies = d.pop("conditionalAccessPolicies")

        tenant_backup_objects_summary_response = cls(
            azure_tenant_id=azure_tenant_id,
            users=users,
            administrative_units=administrative_units,
            groups=groups,
            unified_role_definitions=unified_role_definitions,
            applications=applications,
            service_principals=service_principals,
            arm_role_assignments=arm_role_assignments,
            schema_extensions=schema_extensions,
            unified_role_assignments=unified_role_assignments,
            unified_role_assignment_schedules=unified_role_assignment_schedules,
            unified_role_assignment_schedule_instances=unified_role_assignment_schedule_instances,
            unified_role_eligibility_schedules=unified_role_eligibility_schedules,
            unified_role_eligibility_schedule_instances=unified_role_eligibility_schedule_instances,
            conditional_access_policies=conditional_access_policies,
        )

        tenant_backup_objects_summary_response.additional_properties = d
        return tenant_backup_objects_summary_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
