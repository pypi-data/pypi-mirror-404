from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_archive_retention_policy_settings_model import (
        UnstructuredDataArchiveRetentionPolicySettingsModel,
    )
    from ..models.unstructured_data_archive_settings_model import UnstructuredDataArchiveSettingsModel


T = TypeVar("T", bound="UnstructuredDataBackupJobArchiveRepositoryModel")


@_attrs_define
class UnstructuredDataBackupJobArchiveRepositoryModel:
    """Archive repository settings for unstructured data backup job.

    Attributes:
        archive_repository_id (UUID | Unset): Archive repository ID.
        archive_recent_file_versions (bool | Unset): If `true`, a copy of the data stored in the backup repository will
            also be stored in the archive repository.
        archive_previous_file_versions (bool | Unset): If `true`, Veeam Backup & Replication will archive previous file
            versions.
        archive_retention_policy (UnstructuredDataArchiveRetentionPolicySettingsModel | Unset): Retention policy
            settings.
        file_archive_settings (UnstructuredDataArchiveSettingsModel | Unset): Archive settings for unstructured data
            backup jobs.
    """

    archive_repository_id: UUID | Unset = UNSET
    archive_recent_file_versions: bool | Unset = UNSET
    archive_previous_file_versions: bool | Unset = UNSET
    archive_retention_policy: UnstructuredDataArchiveRetentionPolicySettingsModel | Unset = UNSET
    file_archive_settings: UnstructuredDataArchiveSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        archive_repository_id: str | Unset = UNSET
        if not isinstance(self.archive_repository_id, Unset):
            archive_repository_id = str(self.archive_repository_id)

        archive_recent_file_versions = self.archive_recent_file_versions

        archive_previous_file_versions = self.archive_previous_file_versions

        archive_retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.archive_retention_policy, Unset):
            archive_retention_policy = self.archive_retention_policy.to_dict()

        file_archive_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.file_archive_settings, Unset):
            file_archive_settings = self.file_archive_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if archive_repository_id is not UNSET:
            field_dict["archiveRepositoryId"] = archive_repository_id
        if archive_recent_file_versions is not UNSET:
            field_dict["archiveRecentFileVersions"] = archive_recent_file_versions
        if archive_previous_file_versions is not UNSET:
            field_dict["archivePreviousFileVersions"] = archive_previous_file_versions
        if archive_retention_policy is not UNSET:
            field_dict["archiveRetentionPolicy"] = archive_retention_policy
        if file_archive_settings is not UNSET:
            field_dict["fileArchiveSettings"] = file_archive_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_archive_retention_policy_settings_model import (
            UnstructuredDataArchiveRetentionPolicySettingsModel,
        )
        from ..models.unstructured_data_archive_settings_model import UnstructuredDataArchiveSettingsModel

        d = dict(src_dict)
        _archive_repository_id = d.pop("archiveRepositoryId", UNSET)
        archive_repository_id: UUID | Unset
        if isinstance(_archive_repository_id, Unset):
            archive_repository_id = UNSET
        else:
            archive_repository_id = UUID(_archive_repository_id)

        archive_recent_file_versions = d.pop("archiveRecentFileVersions", UNSET)

        archive_previous_file_versions = d.pop("archivePreviousFileVersions", UNSET)

        _archive_retention_policy = d.pop("archiveRetentionPolicy", UNSET)
        archive_retention_policy: UnstructuredDataArchiveRetentionPolicySettingsModel | Unset
        if isinstance(_archive_retention_policy, Unset):
            archive_retention_policy = UNSET
        else:
            archive_retention_policy = UnstructuredDataArchiveRetentionPolicySettingsModel.from_dict(
                _archive_retention_policy
            )

        _file_archive_settings = d.pop("fileArchiveSettings", UNSET)
        file_archive_settings: UnstructuredDataArchiveSettingsModel | Unset
        if isinstance(_file_archive_settings, Unset):
            file_archive_settings = UNSET
        else:
            file_archive_settings = UnstructuredDataArchiveSettingsModel.from_dict(_file_archive_settings)

        unstructured_data_backup_job_archive_repository_model = cls(
            archive_repository_id=archive_repository_id,
            archive_recent_file_versions=archive_recent_file_versions,
            archive_previous_file_versions=archive_previous_file_versions,
            archive_retention_policy=archive_retention_policy,
            file_archive_settings=file_archive_settings,
        )

        unstructured_data_backup_job_archive_repository_model.additional_properties = d
        return unstructured_data_backup_job_archive_repository_model

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
