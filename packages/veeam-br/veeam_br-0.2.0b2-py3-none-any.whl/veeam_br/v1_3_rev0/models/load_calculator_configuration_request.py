from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LoadCalculatorConfigurationRequest")


@_attrs_define
class LoadCalculatorConfigurationRequest:
    """Load calculator configuration settings.

    Attributes:
        avg_administrative_units_per_minute_backup_count (int | Unset): Average number of administrative units backed up
            in a minute.
        avg_arm_role_assignments_per_minute_backup_count (int | Unset): Average number of ARM role assignments backed up
            in a minute.
        avg_applications_per_minute_backup_count (int | Unset): Average number of applications backed up in a minute.
        avg_conditional_access_policies_per_minute_backup_count (int | Unset): Average number of Conditional Access
            policies backed up in a minute.
        avg_groups_per_minute_backup_count (int | Unset): Average number of groups backed up in a minute.
        avg_schema_extensions_per_minute_backup_count (int | Unset): Average number of schema extensions backed up in a
            minute.
        avg_service_principals_per_minute_backup_count (int | Unset): Average number of service principals backed up in
            a minute.
        avg_users_per_minute_backup_count (int | Unset): Average number of users backed up in a minute.
        avg_unified_role_assignments_per_minute_backup_count (int | Unset): Average number of unified role assignments
            backed up in a minute.
        avg_unified_role_assignment_schedules_per_minute_backup_count (int | Unset): Average number of unified role
            assignment schedules backed up in a minute.
        avg_unified_role_assignment_schedule_instances_per_minute_backup_count (int | Unset): Average number of unified
            role assignment schedule instances backed up in a minute.
        avg_unified_role_definitions_per_minute_backup_count (int | Unset): Average number of ARM role definitions
            backed up in a minute.
        avg_unified_role_eligibility_schedule_per_minute_backup_count (int | Unset): Average number of unified role
            eligibility schedules backed up in a minute.
        avg_unified_role_eligibility_schedule_instance_per_minute_backup_count (int | Unset): Average number of unified
            role eligibility schedule instances backed up in a minute.
        avg_cpu_consumption_count (int | Unset): Average CPU consumption.
        avg_ram_consumption_mb (int | Unset): Average RAM consuption in MB.
        vbr_reserved_ram_consumption_mb (int | Unset): The amount of RAM the Load Calculator reserves for Veeam Backup &
            Replication.
        resources_consumption_soft_issue_threshold (int | Unset): Soft threshold for resource consumption.
        resources_consumption_hard_issue_threshold (int | Unset): Hard threshold for resource consumption.
        tenant_restore_cpu_consumption (float | Unset): CPU consumption for tenant restore.
        tenant_restore_percentage (float | Unset): Tenant restore percentage.
        cpu_allocation_for_backup (float | Unset): CPU allocation for tenant backup.
        cpu_allocation_for_restore (float | Unset): CPU allocation for tenant restore.
        dummy_azure_tenant_id (UUID | Unset): ID assigned by Microsoft Entra to a dummy tenant used by the Load
            Calculator for statistics collection. The tenant is added to Veeam Backup & Replication.
        tenant_reservation_lifetime_minutes (int | Unset): Tenant time reservation, in minutes.
    """

    avg_administrative_units_per_minute_backup_count: int | Unset = UNSET
    avg_arm_role_assignments_per_minute_backup_count: int | Unset = UNSET
    avg_applications_per_minute_backup_count: int | Unset = UNSET
    avg_conditional_access_policies_per_minute_backup_count: int | Unset = UNSET
    avg_groups_per_minute_backup_count: int | Unset = UNSET
    avg_schema_extensions_per_minute_backup_count: int | Unset = UNSET
    avg_service_principals_per_minute_backup_count: int | Unset = UNSET
    avg_users_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_assignments_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_assignment_schedules_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_assignment_schedule_instances_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_definitions_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_eligibility_schedule_per_minute_backup_count: int | Unset = UNSET
    avg_unified_role_eligibility_schedule_instance_per_minute_backup_count: int | Unset = UNSET
    avg_cpu_consumption_count: int | Unset = UNSET
    avg_ram_consumption_mb: int | Unset = UNSET
    vbr_reserved_ram_consumption_mb: int | Unset = UNSET
    resources_consumption_soft_issue_threshold: int | Unset = UNSET
    resources_consumption_hard_issue_threshold: int | Unset = UNSET
    tenant_restore_cpu_consumption: float | Unset = UNSET
    tenant_restore_percentage: float | Unset = UNSET
    cpu_allocation_for_backup: float | Unset = UNSET
    cpu_allocation_for_restore: float | Unset = UNSET
    dummy_azure_tenant_id: UUID | Unset = UNSET
    tenant_reservation_lifetime_minutes: int | Unset = UNSET
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

        dummy_azure_tenant_id: str | Unset = UNSET
        if not isinstance(self.dummy_azure_tenant_id, Unset):
            dummy_azure_tenant_id = str(self.dummy_azure_tenant_id)

        tenant_reservation_lifetime_minutes = self.tenant_reservation_lifetime_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if avg_administrative_units_per_minute_backup_count is not UNSET:
            field_dict["avgAdministrativeUnitsPerMinuteBackupCount"] = avg_administrative_units_per_minute_backup_count
        if avg_arm_role_assignments_per_minute_backup_count is not UNSET:
            field_dict["avgArmRoleAssignmentsPerMinuteBackupCount"] = avg_arm_role_assignments_per_minute_backup_count
        if avg_applications_per_minute_backup_count is not UNSET:
            field_dict["avgApplicationsPerMinuteBackupCount"] = avg_applications_per_minute_backup_count
        if avg_conditional_access_policies_per_minute_backup_count is not UNSET:
            field_dict["avgConditionalAccessPoliciesPerMinuteBackupCount"] = (
                avg_conditional_access_policies_per_minute_backup_count
            )
        if avg_groups_per_minute_backup_count is not UNSET:
            field_dict["avgGroupsPerMinuteBackupCount"] = avg_groups_per_minute_backup_count
        if avg_schema_extensions_per_minute_backup_count is not UNSET:
            field_dict["avgSchemaExtensionsPerMinuteBackupCount"] = avg_schema_extensions_per_minute_backup_count
        if avg_service_principals_per_minute_backup_count is not UNSET:
            field_dict["avgServicePrincipalsPerMinuteBackupCount"] = avg_service_principals_per_minute_backup_count
        if avg_users_per_minute_backup_count is not UNSET:
            field_dict["avgUsersPerMinuteBackupCount"] = avg_users_per_minute_backup_count
        if avg_unified_role_assignments_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleAssignmentsPerMinuteBackupCount"] = (
                avg_unified_role_assignments_per_minute_backup_count
            )
        if avg_unified_role_assignment_schedules_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleAssignmentSchedulesPerMinuteBackupCount"] = (
                avg_unified_role_assignment_schedules_per_minute_backup_count
            )
        if avg_unified_role_assignment_schedule_instances_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleAssignmentScheduleInstancesPerMinuteBackupCount"] = (
                avg_unified_role_assignment_schedule_instances_per_minute_backup_count
            )
        if avg_unified_role_definitions_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleDefinitionsPerMinuteBackupCount"] = (
                avg_unified_role_definitions_per_minute_backup_count
            )
        if avg_unified_role_eligibility_schedule_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleEligibilitySchedulePerMinuteBackupCount"] = (
                avg_unified_role_eligibility_schedule_per_minute_backup_count
            )
        if avg_unified_role_eligibility_schedule_instance_per_minute_backup_count is not UNSET:
            field_dict["avgUnifiedRoleEligibilityScheduleInstancePerMinuteBackupCount"] = (
                avg_unified_role_eligibility_schedule_instance_per_minute_backup_count
            )
        if avg_cpu_consumption_count is not UNSET:
            field_dict["avgCpuConsumptionCount"] = avg_cpu_consumption_count
        if avg_ram_consumption_mb is not UNSET:
            field_dict["avgRamConsumptionMb"] = avg_ram_consumption_mb
        if vbr_reserved_ram_consumption_mb is not UNSET:
            field_dict["vbrReservedRamConsumptionMb"] = vbr_reserved_ram_consumption_mb
        if resources_consumption_soft_issue_threshold is not UNSET:
            field_dict["resourcesConsumptionSoftIssueThreshold"] = resources_consumption_soft_issue_threshold
        if resources_consumption_hard_issue_threshold is not UNSET:
            field_dict["resourcesConsumptionHardIssueThreshold"] = resources_consumption_hard_issue_threshold
        if tenant_restore_cpu_consumption is not UNSET:
            field_dict["tenantRestoreCpuConsumption"] = tenant_restore_cpu_consumption
        if tenant_restore_percentage is not UNSET:
            field_dict["tenantRestorePercentage"] = tenant_restore_percentage
        if cpu_allocation_for_backup is not UNSET:
            field_dict["cpuAllocationForBackup"] = cpu_allocation_for_backup
        if cpu_allocation_for_restore is not UNSET:
            field_dict["cpuAllocationForRestore"] = cpu_allocation_for_restore
        if dummy_azure_tenant_id is not UNSET:
            field_dict["dummyAzureTenantId"] = dummy_azure_tenant_id
        if tenant_reservation_lifetime_minutes is not UNSET:
            field_dict["tenantReservationLifetimeMinutes"] = tenant_reservation_lifetime_minutes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_administrative_units_per_minute_backup_count = d.pop("avgAdministrativeUnitsPerMinuteBackupCount", UNSET)

        avg_arm_role_assignments_per_minute_backup_count = d.pop("avgArmRoleAssignmentsPerMinuteBackupCount", UNSET)

        avg_applications_per_minute_backup_count = d.pop("avgApplicationsPerMinuteBackupCount", UNSET)

        avg_conditional_access_policies_per_minute_backup_count = d.pop(
            "avgConditionalAccessPoliciesPerMinuteBackupCount", UNSET
        )

        avg_groups_per_minute_backup_count = d.pop("avgGroupsPerMinuteBackupCount", UNSET)

        avg_schema_extensions_per_minute_backup_count = d.pop("avgSchemaExtensionsPerMinuteBackupCount", UNSET)

        avg_service_principals_per_minute_backup_count = d.pop("avgServicePrincipalsPerMinuteBackupCount", UNSET)

        avg_users_per_minute_backup_count = d.pop("avgUsersPerMinuteBackupCount", UNSET)

        avg_unified_role_assignments_per_minute_backup_count = d.pop(
            "avgUnifiedRoleAssignmentsPerMinuteBackupCount", UNSET
        )

        avg_unified_role_assignment_schedules_per_minute_backup_count = d.pop(
            "avgUnifiedRoleAssignmentSchedulesPerMinuteBackupCount", UNSET
        )

        avg_unified_role_assignment_schedule_instances_per_minute_backup_count = d.pop(
            "avgUnifiedRoleAssignmentScheduleInstancesPerMinuteBackupCount", UNSET
        )

        avg_unified_role_definitions_per_minute_backup_count = d.pop(
            "avgUnifiedRoleDefinitionsPerMinuteBackupCount", UNSET
        )

        avg_unified_role_eligibility_schedule_per_minute_backup_count = d.pop(
            "avgUnifiedRoleEligibilitySchedulePerMinuteBackupCount", UNSET
        )

        avg_unified_role_eligibility_schedule_instance_per_minute_backup_count = d.pop(
            "avgUnifiedRoleEligibilityScheduleInstancePerMinuteBackupCount", UNSET
        )

        avg_cpu_consumption_count = d.pop("avgCpuConsumptionCount", UNSET)

        avg_ram_consumption_mb = d.pop("avgRamConsumptionMb", UNSET)

        vbr_reserved_ram_consumption_mb = d.pop("vbrReservedRamConsumptionMb", UNSET)

        resources_consumption_soft_issue_threshold = d.pop("resourcesConsumptionSoftIssueThreshold", UNSET)

        resources_consumption_hard_issue_threshold = d.pop("resourcesConsumptionHardIssueThreshold", UNSET)

        tenant_restore_cpu_consumption = d.pop("tenantRestoreCpuConsumption", UNSET)

        tenant_restore_percentage = d.pop("tenantRestorePercentage", UNSET)

        cpu_allocation_for_backup = d.pop("cpuAllocationForBackup", UNSET)

        cpu_allocation_for_restore = d.pop("cpuAllocationForRestore", UNSET)

        _dummy_azure_tenant_id = d.pop("dummyAzureTenantId", UNSET)
        dummy_azure_tenant_id: UUID | Unset
        if isinstance(_dummy_azure_tenant_id, Unset):
            dummy_azure_tenant_id = UNSET
        else:
            dummy_azure_tenant_id = UUID(_dummy_azure_tenant_id)

        tenant_reservation_lifetime_minutes = d.pop("tenantReservationLifetimeMinutes", UNSET)

        load_calculator_configuration_request = cls(
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

        load_calculator_configuration_request.additional_properties = d
        return load_calculator_configuration_request

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
