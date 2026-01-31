from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
    from ..models.gfs_policy_settings_model import GFSPolicySettingsModel
    from ..models.hyper_v_backup_job_advanced_settings_model import HyperVBackupJobAdvancedSettingsModel
    from ..models.hyper_v_backup_proxies_settings_model import HyperVBackupProxiesSettingsModel


T = TypeVar("T", bound="HyperVBackupJobStorageModel")


@_attrs_define
class HyperVBackupJobStorageModel:
    """Microsoft Hyper-V backup storage settings.

    Attributes:
        backup_repository_id (UUID): Backup repository ID.
        backup_proxies (HyperVBackupProxiesSettingsModel): Microsoft Hyper-V backup proxy settings.
        retention_policy (BackupJobRetentionPolicySettingsModel): Retention policy settings.
        gfs_policy (GFSPolicySettingsModel | Unset): GFS retention policy settings.
        advanced_settings (HyperVBackupJobAdvancedSettingsModel | Unset): Advanced backup job settings.
    """

    backup_repository_id: UUID
    backup_proxies: HyperVBackupProxiesSettingsModel
    retention_policy: BackupJobRetentionPolicySettingsModel
    gfs_policy: GFSPolicySettingsModel | Unset = UNSET
    advanced_settings: HyperVBackupJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_repository_id = str(self.backup_repository_id)

        backup_proxies = self.backup_proxies.to_dict()

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
                "backupProxies": backup_proxies,
                "retentionPolicy": retention_policy,
            }
        )
        if gfs_policy is not UNSET:
            field_dict["gfsPolicy"] = gfs_policy
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
        from ..models.gfs_policy_settings_model import GFSPolicySettingsModel
        from ..models.hyper_v_backup_job_advanced_settings_model import HyperVBackupJobAdvancedSettingsModel
        from ..models.hyper_v_backup_proxies_settings_model import HyperVBackupProxiesSettingsModel

        d = dict(src_dict)
        backup_repository_id = UUID(d.pop("backupRepositoryId"))

        backup_proxies = HyperVBackupProxiesSettingsModel.from_dict(d.pop("backupProxies"))

        retention_policy = BackupJobRetentionPolicySettingsModel.from_dict(d.pop("retentionPolicy"))

        _gfs_policy = d.pop("gfsPolicy", UNSET)
        gfs_policy: GFSPolicySettingsModel | Unset
        if isinstance(_gfs_policy, Unset):
            gfs_policy = UNSET
        else:
            gfs_policy = GFSPolicySettingsModel.from_dict(_gfs_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: HyperVBackupJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = HyperVBackupJobAdvancedSettingsModel.from_dict(_advanced_settings)

        hyper_v_backup_job_storage_model = cls(
            backup_repository_id=backup_repository_id,
            backup_proxies=backup_proxies,
            retention_policy=retention_policy,
            gfs_policy=gfs_policy,
            advanced_settings=advanced_settings,
        )

        hyper_v_backup_job_storage_model.additional_properties = d
        return hyper_v_backup_job_storage_model

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
