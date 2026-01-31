from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
    from ..models.file_backup_copy_job_schedule_model import FileBackupCopyJobScheduleModel
    from ..models.file_backup_retention_policy_settings_model import FileBackupRetentionPolicySettingsModel


T = TypeVar("T", bound="FileBackupCopyJobModel")


@_attrs_define
class FileBackupCopyJobModel:
    """
    Attributes:
        id (UUID): ID of the job.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        is_disabled (bool): If `true`, the job is disabled.
        primary_job_id (UUID):
        backup_repository_id (UUID):
        use_custom_retention (bool | Unset):
        retention_policy (FileBackupRetentionPolicySettingsModel | Unset):
        use_custom_encryption (bool | Unset):
        encryption (BackupStorageSettingsEncryptionModel | Unset): Encryption of backup files.
        schedule (FileBackupCopyJobScheduleModel | Unset):
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    primary_job_id: UUID
    backup_repository_id: UUID
    use_custom_retention: bool | Unset = UNSET
    retention_policy: FileBackupRetentionPolicySettingsModel | Unset = UNSET
    use_custom_encryption: bool | Unset = UNSET
    encryption: BackupStorageSettingsEncryptionModel | Unset = UNSET
    schedule: FileBackupCopyJobScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        primary_job_id = str(self.primary_job_id)

        backup_repository_id = str(self.backup_repository_id)

        use_custom_retention = self.use_custom_retention

        retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retention_policy, Unset):
            retention_policy = self.retention_policy.to_dict()

        use_custom_encryption = self.use_custom_encryption

        encryption: dict[str, Any] | Unset = UNSET
        if not isinstance(self.encryption, Unset):
            encryption = self.encryption.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "isDisabled": is_disabled,
                "primaryJobId": primary_job_id,
                "backupRepositoryId": backup_repository_id,
            }
        )
        if use_custom_retention is not UNSET:
            field_dict["useCustomRetention"] = use_custom_retention
        if retention_policy is not UNSET:
            field_dict["retentionPolicy"] = retention_policy
        if use_custom_encryption is not UNSET:
            field_dict["useCustomEncryption"] = use_custom_encryption
        if encryption is not UNSET:
            field_dict["encryption"] = encryption
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
        from ..models.file_backup_copy_job_schedule_model import FileBackupCopyJobScheduleModel
        from ..models.file_backup_retention_policy_settings_model import FileBackupRetentionPolicySettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        primary_job_id = UUID(d.pop("primaryJobId"))

        backup_repository_id = UUID(d.pop("backupRepositoryId"))

        use_custom_retention = d.pop("useCustomRetention", UNSET)

        _retention_policy = d.pop("retentionPolicy", UNSET)
        retention_policy: FileBackupRetentionPolicySettingsModel | Unset
        if isinstance(_retention_policy, Unset):
            retention_policy = UNSET
        else:
            retention_policy = FileBackupRetentionPolicySettingsModel.from_dict(_retention_policy)

        use_custom_encryption = d.pop("useCustomEncryption", UNSET)

        _encryption = d.pop("encryption", UNSET)
        encryption: BackupStorageSettingsEncryptionModel | Unset
        if isinstance(_encryption, Unset):
            encryption = UNSET
        else:
            encryption = BackupStorageSettingsEncryptionModel.from_dict(_encryption)

        _schedule = d.pop("schedule", UNSET)
        schedule: FileBackupCopyJobScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = FileBackupCopyJobScheduleModel.from_dict(_schedule)

        file_backup_copy_job_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
            primary_job_id=primary_job_id,
            backup_repository_id=backup_repository_id,
            use_custom_retention=use_custom_retention,
            retention_policy=retention_policy,
            use_custom_encryption=use_custom_encryption,
            encryption=encryption,
            schedule=schedule,
        )

        file_backup_copy_job_model.additional_properties = d
        return file_backup_copy_job_model

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
