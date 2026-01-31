from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_copy_gfs_policy_settings_model import BackupCopyGFSPolicySettingsModel
    from ..models.backup_copy_job_advanced_settings_model import BackupCopyJobAdvancedSettingsModel
    from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel


T = TypeVar("T", bound="BackupCopyJobTargetModel")


@_attrs_define
class BackupCopyJobTargetModel:
    """Target repository for backup copy job.

    Attributes:
        backup_repository_id (UUID): Backup repository ID.
        retention_policy (BackupJobRetentionPolicySettingsModel | Unset): Retention policy settings.
        gfs_policy (BackupCopyGFSPolicySettingsModel | Unset): GFS retention policy settings.
        advanced_settings (BackupCopyJobAdvancedSettingsModel | Unset): Advanced settings for backup copy job.
    """

    backup_repository_id: UUID
    retention_policy: BackupJobRetentionPolicySettingsModel | Unset = UNSET
    gfs_policy: BackupCopyGFSPolicySettingsModel | Unset = UNSET
    advanced_settings: BackupCopyJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_repository_id = str(self.backup_repository_id)

        retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retention_policy, Unset):
            retention_policy = self.retention_policy.to_dict()

        gfs_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gfs_policy, Unset):
            gfs_policy = self.gfs_policy.to_dict()

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupRepositoryId": backup_repository_id,
            }
        )
        if retention_policy is not UNSET:
            field_dict["retentionPolicy"] = retention_policy
        if gfs_policy is not UNSET:
            field_dict["gfsPolicy"] = gfs_policy
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_copy_gfs_policy_settings_model import BackupCopyGFSPolicySettingsModel
        from ..models.backup_copy_job_advanced_settings_model import BackupCopyJobAdvancedSettingsModel
        from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel

        d = dict(src_dict)
        backup_repository_id = UUID(d.pop("backupRepositoryId"))

        _retention_policy = d.pop("retentionPolicy", UNSET)
        retention_policy: BackupJobRetentionPolicySettingsModel | Unset
        if isinstance(_retention_policy, Unset):
            retention_policy = UNSET
        else:
            retention_policy = BackupJobRetentionPolicySettingsModel.from_dict(_retention_policy)

        _gfs_policy = d.pop("gfsPolicy", UNSET)
        gfs_policy: BackupCopyGFSPolicySettingsModel | Unset
        if isinstance(_gfs_policy, Unset):
            gfs_policy = UNSET
        else:
            gfs_policy = BackupCopyGFSPolicySettingsModel.from_dict(_gfs_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: BackupCopyJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = BackupCopyJobAdvancedSettingsModel.from_dict(_advanced_settings)

        backup_copy_job_target_model = cls(
            backup_repository_id=backup_repository_id,
            retention_policy=retention_policy,
            gfs_policy=gfs_policy,
            advanced_settings=advanced_settings,
        )

        backup_copy_job_target_model.additional_properties = d
        return backup_copy_job_target_model

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
