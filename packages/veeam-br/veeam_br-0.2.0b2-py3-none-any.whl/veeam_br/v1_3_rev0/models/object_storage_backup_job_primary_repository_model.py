from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_backup_job_advanced_settings_model import ObjectStorageBackupJobAdvancedSettingsModel
    from ..models.unstructured_data_retention_policy_settings_model import UnstructuredDataRetentionPolicySettingsModel


T = TypeVar("T", bound="ObjectStorageBackupJobPrimaryRepositoryModel")


@_attrs_define
class ObjectStorageBackupJobPrimaryRepositoryModel:
    """Primary repository settings for object storage backup jobs.

    Attributes:
        backup_repository_id (UUID | Unset): Backup repository ID.
        source_backup_id (UUID | Unset): Source backup ID.
        retention_policy (UnstructuredDataRetentionPolicySettingsModel | Unset): Retention policy settings for
            unstructured data backups.
        advanced_settings (ObjectStorageBackupJobAdvancedSettingsModel | Unset): Advanced settings for object storage
            backup job.
    """

    backup_repository_id: UUID | Unset = UNSET
    source_backup_id: UUID | Unset = UNSET
    retention_policy: UnstructuredDataRetentionPolicySettingsModel | Unset = UNSET
    advanced_settings: ObjectStorageBackupJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_repository_id: str | Unset = UNSET
        if not isinstance(self.backup_repository_id, Unset):
            backup_repository_id = str(self.backup_repository_id)

        source_backup_id: str | Unset = UNSET
        if not isinstance(self.source_backup_id, Unset):
            source_backup_id = str(self.source_backup_id)

        retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retention_policy, Unset):
            retention_policy = self.retention_policy.to_dict()

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_repository_id is not UNSET:
            field_dict["backupRepositoryId"] = backup_repository_id
        if source_backup_id is not UNSET:
            field_dict["sourceBackupId"] = source_backup_id
        if retention_policy is not UNSET:
            field_dict["retentionPolicy"] = retention_policy
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_backup_job_advanced_settings_model import (
            ObjectStorageBackupJobAdvancedSettingsModel,
        )
        from ..models.unstructured_data_retention_policy_settings_model import (
            UnstructuredDataRetentionPolicySettingsModel,
        )

        d = dict(src_dict)
        _backup_repository_id = d.pop("backupRepositoryId", UNSET)
        backup_repository_id: UUID | Unset
        if isinstance(_backup_repository_id, Unset):
            backup_repository_id = UNSET
        else:
            backup_repository_id = UUID(_backup_repository_id)

        _source_backup_id = d.pop("sourceBackupId", UNSET)
        source_backup_id: UUID | Unset
        if isinstance(_source_backup_id, Unset):
            source_backup_id = UNSET
        else:
            source_backup_id = UUID(_source_backup_id)

        _retention_policy = d.pop("retentionPolicy", UNSET)
        retention_policy: UnstructuredDataRetentionPolicySettingsModel | Unset
        if isinstance(_retention_policy, Unset):
            retention_policy = UNSET
        else:
            retention_policy = UnstructuredDataRetentionPolicySettingsModel.from_dict(_retention_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: ObjectStorageBackupJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = ObjectStorageBackupJobAdvancedSettingsModel.from_dict(_advanced_settings)

        object_storage_backup_job_primary_repository_model = cls(
            backup_repository_id=backup_repository_id,
            source_backup_id=source_backup_id,
            retention_policy=retention_policy,
            advanced_settings=advanced_settings,
        )

        object_storage_backup_job_primary_repository_model.additional_properties = d
        return object_storage_backup_job_primary_repository_model

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
