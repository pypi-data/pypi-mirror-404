from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TenantResponse")


@_attrs_define
class TenantResponse:
    """Tenant items.

    Attributes:
        users (int): Number of users.
        groups (int): Number of groups.
        applications (int): Number of applications.
        administrative_units (int): Number of administrative units.
        roles (int): Number of roles.
        service_principals (int): Number of service principals.
        arm_role_assignments (int): Number of ARM role assignments.
        role_assignments (int): Number of role assignments.
        role_assignment_schedules (int): Number of role assignment schedules.
        role_eligibility_schedules (int): Number of role eligibility schedules.
        conditional_access_policies (int): Number of Conditional Access policies.
    """

    users: int
    groups: int
    applications: int
    administrative_units: int
    roles: int
    service_principals: int
    arm_role_assignments: int
    role_assignments: int
    role_assignment_schedules: int
    role_eligibility_schedules: int
    conditional_access_policies: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        users = self.users

        groups = self.groups

        applications = self.applications

        administrative_units = self.administrative_units

        roles = self.roles

        service_principals = self.service_principals

        arm_role_assignments = self.arm_role_assignments

        role_assignments = self.role_assignments

        role_assignment_schedules = self.role_assignment_schedules

        role_eligibility_schedules = self.role_eligibility_schedules

        conditional_access_policies = self.conditional_access_policies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "users": users,
                "groups": groups,
                "applications": applications,
                "administrativeUnits": administrative_units,
                "roles": roles,
                "servicePrincipals": service_principals,
                "armRoleAssignments": arm_role_assignments,
                "roleAssignments": role_assignments,
                "roleAssignmentSchedules": role_assignment_schedules,
                "roleEligibilitySchedules": role_eligibility_schedules,
                "conditionalAccessPolicies": conditional_access_policies,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        users = d.pop("users")

        groups = d.pop("groups")

        applications = d.pop("applications")

        administrative_units = d.pop("administrativeUnits")

        roles = d.pop("roles")

        service_principals = d.pop("servicePrincipals")

        arm_role_assignments = d.pop("armRoleAssignments")

        role_assignments = d.pop("roleAssignments")

        role_assignment_schedules = d.pop("roleAssignmentSchedules")

        role_eligibility_schedules = d.pop("roleEligibilitySchedules")

        conditional_access_policies = d.pop("conditionalAccessPolicies")

        tenant_response = cls(
            users=users,
            groups=groups,
            applications=applications,
            administrative_units=administrative_units,
            roles=roles,
            service_principals=service_principals,
            arm_role_assignments=arm_role_assignments,
            role_assignments=role_assignments,
            role_assignment_schedules=role_assignment_schedules,
            role_eligibility_schedules=role_eligibility_schedules,
            conditional_access_policies=conditional_access_policies,
        )

        tenant_response.additional_properties = d
        return tenant_response

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
