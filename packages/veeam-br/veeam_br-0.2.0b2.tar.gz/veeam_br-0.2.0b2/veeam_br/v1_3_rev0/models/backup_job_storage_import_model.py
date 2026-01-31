from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_advanced_settings_model import BackupJobAdvancedSettingsModel
    from ..models.backup_job_import_proxies_model import BackupJobImportProxiesModel
    from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
    from ..models.backup_repository_import_model import BackupRepositoryImportModel
    from ..models.gfs_policy_settings_model import GFSPolicySettingsModel


T = TypeVar("T", bound="BackupJobStorageImportModel")


@_attrs_define
class BackupJobStorageImportModel:
    """Backup storage settings.

    Attributes:
        backup_repository (BackupRepositoryImportModel): Backup repository.
        backup_proxies (BackupJobImportProxiesModel): Backup proxies.
        retention_policy (BackupJobRetentionPolicySettingsModel): Retention policy settings.
        gfs_policy (GFSPolicySettingsModel | Unset): GFS retention policy settings.
        advanced_settings (BackupJobAdvancedSettingsModel | Unset): Advanced settings for the VMware vSphere backup job.
    """

    backup_repository: BackupRepositoryImportModel
    backup_proxies: BackupJobImportProxiesModel
    retention_policy: BackupJobRetentionPolicySettingsModel
    gfs_policy: GFSPolicySettingsModel | Unset = UNSET
    advanced_settings: BackupJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_repository = self.backup_repository.to_dict()

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
                "backupRepository": backup_repository,
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
        from ..models.backup_job_advanced_settings_model import BackupJobAdvancedSettingsModel
        from ..models.backup_job_import_proxies_model import BackupJobImportProxiesModel
        from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
        from ..models.backup_repository_import_model import BackupRepositoryImportModel
        from ..models.gfs_policy_settings_model import GFSPolicySettingsModel

        d = dict(src_dict)
        backup_repository = BackupRepositoryImportModel.from_dict(d.pop("backupRepository"))

        backup_proxies = BackupJobImportProxiesModel.from_dict(d.pop("backupProxies"))

        retention_policy = BackupJobRetentionPolicySettingsModel.from_dict(d.pop("retentionPolicy"))

        _gfs_policy = d.pop("gfsPolicy", UNSET)
        gfs_policy: GFSPolicySettingsModel | Unset
        if isinstance(_gfs_policy, Unset):
            gfs_policy = UNSET
        else:
            gfs_policy = GFSPolicySettingsModel.from_dict(_gfs_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: BackupJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = BackupJobAdvancedSettingsModel.from_dict(_advanced_settings)

        backup_job_storage_import_model = cls(
            backup_repository=backup_repository,
            backup_proxies=backup_proxies,
            retention_policy=retention_policy,
            gfs_policy=gfs_policy,
            advanced_settings=advanced_settings,
        )

        backup_job_storage_import_model.additional_properties = d
        return backup_job_storage_import_model

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
