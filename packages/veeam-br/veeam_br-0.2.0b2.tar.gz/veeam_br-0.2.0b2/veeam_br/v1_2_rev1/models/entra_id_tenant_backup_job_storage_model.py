from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
    from ..models.entra_id_tenant_backup_job_advanced_settings_model import EntraIDTenantBackupJobAdvancedSettingsModel


T = TypeVar("T", bound="EntraIDTenantBackupJobStorageModel")


@_attrs_define
class EntraIDTenantBackupJobStorageModel:
    """Job storage settings.

    Attributes:
        tenant_id (UUID): Tenant ID assigned by Veeam Backup & Replication.
        retention_policy (BackupJobRetentionPolicySettingsModel | Unset): Retention policy settings.
        advanced_settings (EntraIDTenantBackupJobAdvancedSettingsModel | Unset): Advanced job settings.
    """

    tenant_id: UUID
    retention_policy: BackupJobRetentionPolicySettingsModel | Unset = UNSET
    advanced_settings: EntraIDTenantBackupJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = str(self.tenant_id)

        retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retention_policy, Unset):
            retention_policy = self.retention_policy.to_dict()

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenantId": tenant_id,
            }
        )
        if retention_policy is not UNSET:
            field_dict["retentionPolicy"] = retention_policy
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
        from ..models.entra_id_tenant_backup_job_advanced_settings_model import (
            EntraIDTenantBackupJobAdvancedSettingsModel,
        )

        d = dict(src_dict)
        tenant_id = UUID(d.pop("tenantId"))

        _retention_policy = d.pop("retentionPolicy", UNSET)
        retention_policy: BackupJobRetentionPolicySettingsModel | Unset
        if isinstance(_retention_policy, Unset):
            retention_policy = UNSET
        else:
            retention_policy = BackupJobRetentionPolicySettingsModel.from_dict(_retention_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: EntraIDTenantBackupJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = EntraIDTenantBackupJobAdvancedSettingsModel.from_dict(_advanced_settings)

        entra_id_tenant_backup_job_storage_model = cls(
            tenant_id=tenant_id,
            retention_policy=retention_policy,
            advanced_settings=advanced_settings,
        )

        entra_id_tenant_backup_job_storage_model.additional_properties = d
        return entra_id_tenant_backup_job_storage_model

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
