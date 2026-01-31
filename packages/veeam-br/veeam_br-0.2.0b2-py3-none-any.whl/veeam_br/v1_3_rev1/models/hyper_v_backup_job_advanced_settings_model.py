from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_mode_type import EBackupModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.active_full_settings_model import ActiveFullSettingsModel
    from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
    from ..models.backup_job_advanced_settings_hyper_v_model import BackupJobAdvancedSettingsHyperVModel
    from ..models.backup_storage_setting_model import BackupStorageSettingModel
    from ..models.full_backup_maintenance_model import FullBackupMaintenanceModel
    from ..models.job_scripts_settings_model import JobScriptsSettingsModel
    from ..models.notification_settings_model import NotificationSettingsModel
    from ..models.synthetic_full_settings_model import SyntheticFullSettingsModel


T = TypeVar("T", bound="HyperVBackupJobAdvancedSettingsModel")


@_attrs_define
class HyperVBackupJobAdvancedSettingsModel:
    """Advanced backup job settings.

    Attributes:
        backup_mode_type (EBackupModeType): Type of the backup method used to create a restore point.
        synthentic_fulls (SyntheticFullSettingsModel | Unset): Synthetic full backup settings.
        active_fulls (ActiveFullSettingsModel | Unset): Active full backup settings.
        backup_health (BackupHealthCheckSettingsModels | Unset): Health check settings for the latest restore point in
            the backup chain.
        full_backup_maintenance (FullBackupMaintenanceModel | Unset): Maintenance settings for full backup files.
        storage_data (BackupStorageSettingModel | Unset): Storage settings.
        notifications (NotificationSettingsModel | Unset): Notification settings.
        hyper_v (BackupJobAdvancedSettingsHyperVModel | Unset): Microsoft Hyper-V settings for the job.
        scripts (JobScriptsSettingsModel | Unset): Script settings.<ul><li>`preCommand` — script executed before the
            job</li><li>`postCommand` — script executed after the job</li></ul>
    """

    backup_mode_type: EBackupModeType
    synthentic_fulls: SyntheticFullSettingsModel | Unset = UNSET
    active_fulls: ActiveFullSettingsModel | Unset = UNSET
    backup_health: BackupHealthCheckSettingsModels | Unset = UNSET
    full_backup_maintenance: FullBackupMaintenanceModel | Unset = UNSET
    storage_data: BackupStorageSettingModel | Unset = UNSET
    notifications: NotificationSettingsModel | Unset = UNSET
    hyper_v: BackupJobAdvancedSettingsHyperVModel | Unset = UNSET
    scripts: JobScriptsSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_mode_type = self.backup_mode_type.value

        synthentic_fulls: dict[str, Any] | Unset = UNSET
        if not isinstance(self.synthentic_fulls, Unset):
            synthentic_fulls = self.synthentic_fulls.to_dict()

        active_fulls: dict[str, Any] | Unset = UNSET
        if not isinstance(self.active_fulls, Unset):
            active_fulls = self.active_fulls.to_dict()

        backup_health: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_health, Unset):
            backup_health = self.backup_health.to_dict()

        full_backup_maintenance: dict[str, Any] | Unset = UNSET
        if not isinstance(self.full_backup_maintenance, Unset):
            full_backup_maintenance = self.full_backup_maintenance.to_dict()

        storage_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_data, Unset):
            storage_data = self.storage_data.to_dict()

        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        hyper_v: dict[str, Any] | Unset = UNSET
        if not isinstance(self.hyper_v, Unset):
            hyper_v = self.hyper_v.to_dict()

        scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupModeType": backup_mode_type,
            }
        )
        if synthentic_fulls is not UNSET:
            field_dict["synthenticFulls"] = synthentic_fulls
        if active_fulls is not UNSET:
            field_dict["activeFulls"] = active_fulls
        if backup_health is not UNSET:
            field_dict["backupHealth"] = backup_health
        if full_backup_maintenance is not UNSET:
            field_dict["fullBackupMaintenance"] = full_backup_maintenance
        if storage_data is not UNSET:
            field_dict["storageData"] = storage_data
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if hyper_v is not UNSET:
            field_dict["hyperV"] = hyper_v
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.active_full_settings_model import ActiveFullSettingsModel
        from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
        from ..models.backup_job_advanced_settings_hyper_v_model import BackupJobAdvancedSettingsHyperVModel
        from ..models.backup_storage_setting_model import BackupStorageSettingModel
        from ..models.full_backup_maintenance_model import FullBackupMaintenanceModel
        from ..models.job_scripts_settings_model import JobScriptsSettingsModel
        from ..models.notification_settings_model import NotificationSettingsModel
        from ..models.synthetic_full_settings_model import SyntheticFullSettingsModel

        d = dict(src_dict)
        backup_mode_type = EBackupModeType(d.pop("backupModeType"))

        _synthentic_fulls = d.pop("synthenticFulls", UNSET)
        synthentic_fulls: SyntheticFullSettingsModel | Unset
        if isinstance(_synthentic_fulls, Unset):
            synthentic_fulls = UNSET
        else:
            synthentic_fulls = SyntheticFullSettingsModel.from_dict(_synthentic_fulls)

        _active_fulls = d.pop("activeFulls", UNSET)
        active_fulls: ActiveFullSettingsModel | Unset
        if isinstance(_active_fulls, Unset):
            active_fulls = UNSET
        else:
            active_fulls = ActiveFullSettingsModel.from_dict(_active_fulls)

        _backup_health = d.pop("backupHealth", UNSET)
        backup_health: BackupHealthCheckSettingsModels | Unset
        if isinstance(_backup_health, Unset):
            backup_health = UNSET
        else:
            backup_health = BackupHealthCheckSettingsModels.from_dict(_backup_health)

        _full_backup_maintenance = d.pop("fullBackupMaintenance", UNSET)
        full_backup_maintenance: FullBackupMaintenanceModel | Unset
        if isinstance(_full_backup_maintenance, Unset):
            full_backup_maintenance = UNSET
        else:
            full_backup_maintenance = FullBackupMaintenanceModel.from_dict(_full_backup_maintenance)

        _storage_data = d.pop("storageData", UNSET)
        storage_data: BackupStorageSettingModel | Unset
        if isinstance(_storage_data, Unset):
            storage_data = UNSET
        else:
            storage_data = BackupStorageSettingModel.from_dict(_storage_data)

        _notifications = d.pop("notifications", UNSET)
        notifications: NotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = NotificationSettingsModel.from_dict(_notifications)

        _hyper_v = d.pop("hyperV", UNSET)
        hyper_v: BackupJobAdvancedSettingsHyperVModel | Unset
        if isinstance(_hyper_v, Unset):
            hyper_v = UNSET
        else:
            hyper_v = BackupJobAdvancedSettingsHyperVModel.from_dict(_hyper_v)

        _scripts = d.pop("scripts", UNSET)
        scripts: JobScriptsSettingsModel | Unset
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = JobScriptsSettingsModel.from_dict(_scripts)

        hyper_v_backup_job_advanced_settings_model = cls(
            backup_mode_type=backup_mode_type,
            synthentic_fulls=synthentic_fulls,
            active_fulls=active_fulls,
            backup_health=backup_health,
            full_backup_maintenance=full_backup_maintenance,
            storage_data=storage_data,
            notifications=notifications,
            hyper_v=hyper_v,
            scripts=scripts,
        )

        hyper_v_backup_job_advanced_settings_model.additional_properties = d
        return hyper_v_backup_job_advanced_settings_model

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
