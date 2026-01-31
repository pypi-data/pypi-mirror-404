from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LoadCalculatorConfigurationResponse")


@_attrs_define
class LoadCalculatorConfigurationResponse:
    """Load calculator configuration.

    Attributes:
        avg_administrative_units_per_minute_backup_count (int): Average number of administrative units backed up in a
            minute.
        avg_arm_role_assignments_per_minute_backup_count (int): Average number of ARM role assignments backed up in a
            minute.
        avg_applications_per_minute_backup_count (int): Average number of applications backed up in a minute.
        avg_conditional_access_policies_per_minute_backup_count (int): Average number of Conditional Access policies
            backed up in a minute.
        avg_groups_per_minute_backup_count (int): Average number of groups backed up in a minute.
        avg_schema_extensions_per_minute_backup_count (int): Average number of schema extensions backed up in a minute.
        avg_service_principals_per_minute_backup_count (int): Average number of service principals backed up in a
            minute.
        avg_users_per_minute_backup_count (int): Average number of users backed up in a minute.
        avg_unified_role_assignments_per_minute_backup_count (int): Average number of unified role assignments backed up
            in a minute.
        avg_unified_role_assignment_schedules_per_minute_backup_count (int): Average number of unified role assignment
            schedules backed up in a minute.
        avg_unified_role_assignment_schedule_instances_per_minute_backup_count (int): Average number of unified role
            assignment schedule instances backed up in a minute.
        avg_unified_role_definitions_per_minute_backup_count (int): Average number of ARM role definitions backed up in
            a minute.
        avg_unified_role_eligibility_schedule_per_minute_backup_count (int): Average number of unified role eligibility
            schedules backed up in a minute.
        avg_unified_role_eligibility_schedule_instance_per_minute_backup_count (int): Average number of unified role
            eligibility schedule instances backed up in a minute.
        avg_cpu_consumption_count (int): Average CPU consumption.
        avg_ram_consumption_mb (int): Average RAM consuption in MB.
        vbr_reserved_ram_consumption_mb (int): The amount of RAM the Load Calculator reserves for Veeam Backup &
            Replication.
        resources_consumption_soft_issue_threshold (int): Soft threshold for resource consumption.
        resources_consumption_hard_issue_threshold (int): Hard threshold for resource consumption.
        tenant_restore_cpu_consumption (float): CPU consumption for tenant restore.
        tenant_restore_percentage (float): Tenant restore percentage.
        cpu_allocation_for_backup (float): CPU allocation for tenant backup.
        cpu_allocation_for_restore (float): CPU allocation for tenant restore.
        dummy_azure_tenant_id (UUID): ID assigned by Microsoft Entra to a dummy tenant used by the Load Calculator for
            statistics collection. The tenant is added to Veeam Backup & Replication.
        tenant_reservation_lifetime_minutes (int): Tenant time reservation, in minutes.
    """

    avg_administrative_units_per_minute_backup_count: int
    avg_arm_role_assignments_per_minute_backup_count: int
    avg_applications_per_minute_backup_count: int
    avg_conditional_access_policies_per_minute_backup_count: int
    avg_groups_per_minute_backup_count: int
    avg_schema_extensions_per_minute_backup_count: int
    avg_service_principals_per_minute_backup_count: int
    avg_users_per_minute_backup_count: int
    avg_unified_role_assignments_per_minute_backup_count: int
    avg_unified_role_assignment_schedules_per_minute_backup_count: int
    avg_unified_role_assignment_schedule_instances_per_minute_backup_count: int
    avg_unified_role_definitions_per_minute_backup_count: int
    avg_unified_role_eligibility_schedule_per_minute_backup_count: int
    avg_unified_role_eligibility_schedule_instance_per_minute_backup_count: int
    avg_cpu_consumption_count: int
    avg_ram_consumption_mb: int
    vbr_reserved_ram_consumption_mb: int
    resources_consumption_soft_issue_threshold: int
    resources_consumption_hard_issue_threshold: int
    tenant_restore_cpu_consumption: float
    tenant_restore_percentage: float
    cpu_allocation_for_backup: float
    cpu_allocation_for_restore: float
    dummy_azure_tenant_id: UUID
    tenant_reservation_lifetime_minutes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_administrative_units_per_minute_backup_count = self.avg_administrative_units_per_minute_backup_count

        avg_arm_role_assignments_per_minute_backup_count = self.avg_arm_role_assignments_per_minute_backup_count

        avg_applications_per_minute_backup_count = self.avg_applications_per_minute_backup_count

        avg_conditional_access_policies_per_minute_backup_count = (
            self.avg_conditional_access_policies_per_minute_backup_count
        )

        avg_groups_per_minute_backup_count = self.avg_groups_per_minute_backup_count

        avg_schema_extensions_per_minute_backup_count = self.avg_schema_extensions_per_minute_backup_count

        avg_service_principals_per_minute_backup_count = self.avg_service_principals_per_minute_backup_count

        avg_users_per_minute_backup_count = self.avg_users_per_minute_backup_count

        avg_unified_role_assignments_per_minute_backup_count = self.avg_unified_role_assignments_per_minute_backup_count

        avg_unified_role_assignment_schedules_per_minute_backup_count = (
            self.avg_unified_role_assignment_schedules_per_minute_backup_count
        )

        avg_unified_role_assignment_schedule_instances_per_minute_backup_count = (
            self.avg_unified_role_assignment_schedule_instances_per_minute_backup_count
        )

        avg_unified_role_definitions_per_minute_backup_count = self.avg_unified_role_definitions_per_minute_backup_count

        avg_unified_role_eligibility_schedule_per_minute_backup_count = (
            self.avg_unified_role_eligibility_schedule_per_minute_backup_count
        )

        avg_unified_role_eligibility_schedule_instance_per_minute_backup_count = (
            self.avg_unified_role_eligibility_schedule_instance_per_minute_backup_count
        )

        avg_cpu_consumption_count = self.avg_cpu_consumption_count

        avg_ram_consumption_mb = self.avg_ram_consumption_mb

        vbr_reserved_ram_consumption_mb = self.vbr_reserved_ram_consumption_mb

        resources_consumption_soft_issue_threshold = self.resources_consumption_soft_issue_threshold

        resources_consumption_hard_issue_threshold = self.resources_consumption_hard_issue_threshold

        tenant_restore_cpu_consumption = self.tenant_restore_cpu_consumption

        tenant_restore_percentage = self.tenant_restore_percentage

        cpu_allocation_for_backup = self.cpu_allocation_for_backup

        cpu_allocation_for_restore = self.cpu_allocation_for_restore

        dummy_azure_tenant_id = str(self.dummy_azure_tenant_id)

        tenant_reservation_lifetime_minutes = self.tenant_reservation_lifetime_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avgAdministrativeUnitsPerMinuteBackupCount": avg_administrative_units_per_minute_backup_count,
                "avgArmRoleAssignmentsPerMinuteBackupCount": avg_arm_role_assignments_per_minute_backup_count,
                "avgApplicationsPerMinuteBackupCount": avg_applications_per_minute_backup_count,
                "avgConditionalAccessPoliciesPerMinuteBackupCount": avg_conditional_access_policies_per_minute_backup_count,
                "avgGroupsPerMinuteBackupCount": avg_groups_per_minute_backup_count,
                "avgSchemaExtensionsPerMinuteBackupCount": avg_schema_extensions_per_minute_backup_count,
                "avgServicePrincipalsPerMinuteBackupCount": avg_service_principals_per_minute_backup_count,
                "avgUsersPerMinuteBackupCount": avg_users_per_minute_backup_count,
                "avgUnifiedRoleAssignmentsPerMinuteBackupCount": avg_unified_role_assignments_per_minute_backup_count,
                "avgUnifiedRoleAssignmentSchedulesPerMinuteBackupCount": avg_unified_role_assignment_schedules_per_minute_backup_count,
                "avgUnifiedRoleAssignmentScheduleInstancesPerMinuteBackupCount": avg_unified_role_assignment_schedule_instances_per_minute_backup_count,
                "avgUnifiedRoleDefinitionsPerMinuteBackupCount": avg_unified_role_definitions_per_minute_backup_count,
                "avgUnifiedRoleEligibilitySchedulePerMinuteBackupCount": avg_unified_role_eligibility_schedule_per_minute_backup_count,
                "avgUnifiedRoleEligibilityScheduleInstancePerMinuteBackupCount": avg_unified_role_eligibility_schedule_instance_per_minute_backup_count,
                "avgCpuConsumptionCount": avg_cpu_consumption_count,
                "avgRamConsumptionMb": avg_ram_consumption_mb,
                "vbrReservedRamConsumptionMb": vbr_reserved_ram_consumption_mb,
                "resourcesConsumptionSoftIssueThreshold": resources_consumption_soft_issue_threshold,
                "resourcesConsumptionHardIssueThreshold": resources_consumption_hard_issue_threshold,
                "tenantRestoreCpuConsumption": tenant_restore_cpu_consumption,
                "tenantRestorePercentage": tenant_restore_percentage,
                "cpuAllocationForBackup": cpu_allocation_for_backup,
                "cpuAllocationForRestore": cpu_allocation_for_restore,
                "dummyAzureTenantId": dummy_azure_tenant_id,
                "tenantReservationLifetimeMinutes": tenant_reservation_lifetime_minutes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_administrative_units_per_minute_backup_count = d.pop("avgAdministrativeUnitsPerMinuteBackupCount")

        avg_arm_role_assignments_per_minute_backup_count = d.pop("avgArmRoleAssignmentsPerMinuteBackupCount")

        avg_applications_per_minute_backup_count = d.pop("avgApplicationsPerMinuteBackupCount")

        avg_conditional_access_policies_per_minute_backup_count = d.pop(
            "avgConditionalAccessPoliciesPerMinuteBackupCount"
        )

        avg_groups_per_minute_backup_count = d.pop("avgGroupsPerMinuteBackupCount")

        avg_schema_extensions_per_minute_backup_count = d.pop("avgSchemaExtensionsPerMinuteBackupCount")

        avg_service_principals_per_minute_backup_count = d.pop("avgServicePrincipalsPerMinuteBackupCount")

        avg_users_per_minute_backup_count = d.pop("avgUsersPerMinuteBackupCount")

        avg_unified_role_assignments_per_minute_backup_count = d.pop("avgUnifiedRoleAssignmentsPerMinuteBackupCount")

        avg_unified_role_assignment_schedules_per_minute_backup_count = d.pop(
            "avgUnifiedRoleAssignmentSchedulesPerMinuteBackupCount"
        )

        avg_unified_role_assignment_schedule_instances_per_minute_backup_count = d.pop(
            "avgUnifiedRoleAssignmentScheduleInstancesPerMinuteBackupCount"
        )

        avg_unified_role_definitions_per_minute_backup_count = d.pop("avgUnifiedRoleDefinitionsPerMinuteBackupCount")

        avg_unified_role_eligibility_schedule_per_minute_backup_count = d.pop(
            "avgUnifiedRoleEligibilitySchedulePerMinuteBackupCount"
        )

        avg_unified_role_eligibility_schedule_instance_per_minute_backup_count = d.pop(
            "avgUnifiedRoleEligibilityScheduleInstancePerMinuteBackupCount"
        )

        avg_cpu_consumption_count = d.pop("avgCpuConsumptionCount")

        avg_ram_consumption_mb = d.pop("avgRamConsumptionMb")

        vbr_reserved_ram_consumption_mb = d.pop("vbrReservedRamConsumptionMb")

        resources_consumption_soft_issue_threshold = d.pop("resourcesConsumptionSoftIssueThreshold")

        resources_consumption_hard_issue_threshold = d.pop("resourcesConsumptionHardIssueThreshold")

        tenant_restore_cpu_consumption = d.pop("tenantRestoreCpuConsumption")

        tenant_restore_percentage = d.pop("tenantRestorePercentage")

        cpu_allocation_for_backup = d.pop("cpuAllocationForBackup")

        cpu_allocation_for_restore = d.pop("cpuAllocationForRestore")

        dummy_azure_tenant_id = UUID(d.pop("dummyAzureTenantId"))

        tenant_reservation_lifetime_minutes = d.pop("tenantReservationLifetimeMinutes")

        load_calculator_configuration_response = cls(
            avg_administrative_units_per_minute_backup_count=avg_administrative_units_per_minute_backup_count,
            avg_arm_role_assignments_per_minute_backup_count=avg_arm_role_assignments_per_minute_backup_count,
            avg_applications_per_minute_backup_count=avg_applications_per_minute_backup_count,
            avg_conditional_access_policies_per_minute_backup_count=avg_conditional_access_policies_per_minute_backup_count,
            avg_groups_per_minute_backup_count=avg_groups_per_minute_backup_count,
            avg_schema_extensions_per_minute_backup_count=avg_schema_extensions_per_minute_backup_count,
            avg_service_principals_per_minute_backup_count=avg_service_principals_per_minute_backup_count,
            avg_users_per_minute_backup_count=avg_users_per_minute_backup_count,
            avg_unified_role_assignments_per_minute_backup_count=avg_unified_role_assignments_per_minute_backup_count,
            avg_unified_role_assignment_schedules_per_minute_backup_count=avg_unified_role_assignment_schedules_per_minute_backup_count,
            avg_unified_role_assignment_schedule_instances_per_minute_backup_count=avg_unified_role_assignment_schedule_instances_per_minute_backup_count,
            avg_unified_role_definitions_per_minute_backup_count=avg_unified_role_definitions_per_minute_backup_count,
            avg_unified_role_eligibility_schedule_per_minute_backup_count=avg_unified_role_eligibility_schedule_per_minute_backup_count,
            avg_unified_role_eligibility_schedule_instance_per_minute_backup_count=avg_unified_role_eligibility_schedule_instance_per_minute_backup_count,
            avg_cpu_consumption_count=avg_cpu_consumption_count,
            avg_ram_consumption_mb=avg_ram_consumption_mb,
            vbr_reserved_ram_consumption_mb=vbr_reserved_ram_consumption_mb,
            resources_consumption_soft_issue_threshold=resources_consumption_soft_issue_threshold,
            resources_consumption_hard_issue_threshold=resources_consumption_hard_issue_threshold,
            tenant_restore_cpu_consumption=tenant_restore_cpu_consumption,
            tenant_restore_percentage=tenant_restore_percentage,
            cpu_allocation_for_backup=cpu_allocation_for_backup,
            cpu_allocation_for_restore=cpu_allocation_for_restore,
            dummy_azure_tenant_id=dummy_azure_tenant_id,
            tenant_reservation_lifetime_minutes=tenant_reservation_lifetime_minutes,
        )

        load_calculator_configuration_response.additional_properties = d
        return load_calculator_configuration_response

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
