from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.config_backup_encryption_model import ConfigBackupEncryptionModel
    from ..models.config_backup_last_successful_model import ConfigBackupLastSuccessfulModel
    from ..models.config_backup_notifications_model import ConfigBackupNotificationsModel
    from ..models.config_backup_schedule_model import ConfigBackupScheduleModel


T = TypeVar("T", bound="ConfigBackupModel")


@_attrs_define
class ConfigBackupModel:
    """Configuration backup.

    Attributes:
        is_enabled (bool): If `true`, configuration backup is enabled.
        backup_repository_id (UUID): ID of the backup repository on which the configuration backup is stored.
        restore_points_to_keep (int): Number of restore points to keep in the backup repository.
        notifications (ConfigBackupNotificationsModel): Notification settings.
        schedule (ConfigBackupScheduleModel): Scheduling settings.
        last_successful_backup (ConfigBackupLastSuccessfulModel): Last successful backup.
        encryption (ConfigBackupEncryptionModel): Encryption settings.
    """

    is_enabled: bool
    backup_repository_id: UUID
    restore_points_to_keep: int
    notifications: ConfigBackupNotificationsModel
    schedule: ConfigBackupScheduleModel
    last_successful_backup: ConfigBackupLastSuccessfulModel
    encryption: ConfigBackupEncryptionModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        backup_repository_id = str(self.backup_repository_id)

        restore_points_to_keep = self.restore_points_to_keep

        notifications = self.notifications.to_dict()

        schedule = self.schedule.to_dict()

        last_successful_backup = self.last_successful_backup.to_dict()

        encryption = self.encryption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
                "backupRepositoryId": backup_repository_id,
                "restorePointsToKeep": restore_points_to_keep,
                "notifications": notifications,
                "schedule": schedule,
                "lastSuccessfulBackup": last_successful_backup,
                "encryption": encryption,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.config_backup_encryption_model import ConfigBackupEncryptionModel
        from ..models.config_backup_last_successful_model import ConfigBackupLastSuccessfulModel
        from ..models.config_backup_notifications_model import ConfigBackupNotificationsModel
        from ..models.config_backup_schedule_model import ConfigBackupScheduleModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        backup_repository_id = UUID(d.pop("backupRepositoryId"))

        restore_points_to_keep = d.pop("restorePointsToKeep")

        notifications = ConfigBackupNotificationsModel.from_dict(d.pop("notifications"))

        schedule = ConfigBackupScheduleModel.from_dict(d.pop("schedule"))

        last_successful_backup = ConfigBackupLastSuccessfulModel.from_dict(d.pop("lastSuccessfulBackup"))

        encryption = ConfigBackupEncryptionModel.from_dict(d.pop("encryption"))

        config_backup_model = cls(
            is_enabled=is_enabled,
            backup_repository_id=backup_repository_id,
            restore_points_to_keep=restore_points_to_keep,
            notifications=notifications,
            schedule=schedule,
            last_successful_backup=last_successful_backup,
            encryption=encryption,
        )

        config_backup_model.additional_properties = d
        return config_backup_model

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
