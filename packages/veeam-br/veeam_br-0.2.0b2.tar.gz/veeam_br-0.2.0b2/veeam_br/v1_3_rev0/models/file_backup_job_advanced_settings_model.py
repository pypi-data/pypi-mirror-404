from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acl_handling_settings_model import ACLHandlingSettingsModel
    from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
    from ..models.backup_item_versions_settings_model import BackupItemVersionsSettingsModel
    from ..models.file_backup_notification_settings_model import FileBackupNotificationSettingsModel
    from ..models.file_backup_storage_settings_model import FileBackupStorageSettingsModel
    from ..models.job_scripts_settings_model import JobScriptsSettingsModel


T = TypeVar("T", bound="FileBackupJobAdvancedSettingsModel")


@_attrs_define
class FileBackupJobAdvancedSettingsModel:
    """Advanced settings for file backup job.

    Attributes:
        file_versions (BackupItemVersionsSettingsModel | Unset): Settings for version-based retention policy.
        acl_handling (ACLHandlingSettingsModel | Unset): ACL handling settings.
        storage_data (FileBackupStorageSettingsModel | Unset): Storage settings for file backup.
        backup_health (BackupHealthCheckSettingsModels | Unset): Health check settings for the latest restore point in
            the backup chain.
        scripts (JobScriptsSettingsModel | Unset): Script settings.<ul><li>`preCommand` — script executed before the
            job</li><li>`postCommand` — script executed after the job</li></ul>
        notifications (FileBackupNotificationSettingsModel | Unset): Notification settings for file backup.
    """

    file_versions: BackupItemVersionsSettingsModel | Unset = UNSET
    acl_handling: ACLHandlingSettingsModel | Unset = UNSET
    storage_data: FileBackupStorageSettingsModel | Unset = UNSET
    backup_health: BackupHealthCheckSettingsModels | Unset = UNSET
    scripts: JobScriptsSettingsModel | Unset = UNSET
    notifications: FileBackupNotificationSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_versions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.file_versions, Unset):
            file_versions = self.file_versions.to_dict()

        acl_handling: dict[str, Any] | Unset = UNSET
        if not isinstance(self.acl_handling, Unset):
            acl_handling = self.acl_handling.to_dict()

        storage_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_data, Unset):
            storage_data = self.storage_data.to_dict()

        backup_health: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_health, Unset):
            backup_health = self.backup_health.to_dict()

        scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_versions is not UNSET:
            field_dict["fileVersions"] = file_versions
        if acl_handling is not UNSET:
            field_dict["aclHandling"] = acl_handling
        if storage_data is not UNSET:
            field_dict["storageData"] = storage_data
        if backup_health is not UNSET:
            field_dict["backupHealth"] = backup_health
        if scripts is not UNSET:
            field_dict["scripts"] = scripts
        if notifications is not UNSET:
            field_dict["notifications"] = notifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acl_handling_settings_model import ACLHandlingSettingsModel
        from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
        from ..models.backup_item_versions_settings_model import BackupItemVersionsSettingsModel
        from ..models.file_backup_notification_settings_model import FileBackupNotificationSettingsModel
        from ..models.file_backup_storage_settings_model import FileBackupStorageSettingsModel
        from ..models.job_scripts_settings_model import JobScriptsSettingsModel

        d = dict(src_dict)
        _file_versions = d.pop("fileVersions", UNSET)
        file_versions: BackupItemVersionsSettingsModel | Unset
        if isinstance(_file_versions, Unset):
            file_versions = UNSET
        else:
            file_versions = BackupItemVersionsSettingsModel.from_dict(_file_versions)

        _acl_handling = d.pop("aclHandling", UNSET)
        acl_handling: ACLHandlingSettingsModel | Unset
        if isinstance(_acl_handling, Unset):
            acl_handling = UNSET
        else:
            acl_handling = ACLHandlingSettingsModel.from_dict(_acl_handling)

        _storage_data = d.pop("storageData", UNSET)
        storage_data: FileBackupStorageSettingsModel | Unset
        if isinstance(_storage_data, Unset):
            storage_data = UNSET
        else:
            storage_data = FileBackupStorageSettingsModel.from_dict(_storage_data)

        _backup_health = d.pop("backupHealth", UNSET)
        backup_health: BackupHealthCheckSettingsModels | Unset
        if isinstance(_backup_health, Unset):
            backup_health = UNSET
        else:
            backup_health = BackupHealthCheckSettingsModels.from_dict(_backup_health)

        _scripts = d.pop("scripts", UNSET)
        scripts: JobScriptsSettingsModel | Unset
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = JobScriptsSettingsModel.from_dict(_scripts)

        _notifications = d.pop("notifications", UNSET)
        notifications: FileBackupNotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = FileBackupNotificationSettingsModel.from_dict(_notifications)

        file_backup_job_advanced_settings_model = cls(
            file_versions=file_versions,
            acl_handling=acl_handling,
            storage_data=storage_data,
            backup_health=backup_health,
            scripts=scripts,
            notifications=notifications,
        )

        file_backup_job_advanced_settings_model.additional_properties = d
        return file_backup_job_advanced_settings_model

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
