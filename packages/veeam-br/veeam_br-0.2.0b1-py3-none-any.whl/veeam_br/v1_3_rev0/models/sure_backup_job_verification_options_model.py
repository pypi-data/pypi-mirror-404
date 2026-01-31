from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sure_backup_job_notification_settings_model import SureBackupJobNotificationSettingsModel


T = TypeVar("T", bound="SureBackupJobVerificationOptionsModel")


@_attrs_define
class SureBackupJobVerificationOptionsModel:
    """SureBackup job verification options.

    Attributes:
        malware_scan_enabled (bool): If `true`, Veeam Backup & Replication will scan VMs with antivirus software.
        yara_scan_enabled (bool): If `true`, Veeam Backup & Replication will scan VMs with the specified YARA rule.
        yara_scan_rule (str | Unset): Yara scan rule that will be used to scan VMs.
        entire_image_scan_enabled (bool | Unset): If `true`, the antivirus software will continue scanning VMs after the
            first malware is found.
        disk_content_validation_enabled (bool | Unset): If `true`, Veeam Backup & Replication will validate backup files
            of VMs with a CRC check to make sure that the file is not corrupted.
        notifications (SureBackupJobNotificationSettingsModel | Unset): SureBackup job notification settings.
    """

    malware_scan_enabled: bool
    yara_scan_enabled: bool
    yara_scan_rule: str | Unset = UNSET
    entire_image_scan_enabled: bool | Unset = UNSET
    disk_content_validation_enabled: bool | Unset = UNSET
    notifications: SureBackupJobNotificationSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        malware_scan_enabled = self.malware_scan_enabled

        yara_scan_enabled = self.yara_scan_enabled

        yara_scan_rule = self.yara_scan_rule

        entire_image_scan_enabled = self.entire_image_scan_enabled

        disk_content_validation_enabled = self.disk_content_validation_enabled

        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "malwareScanEnabled": malware_scan_enabled,
                "yaraScanEnabled": yara_scan_enabled,
            }
        )
        if yara_scan_rule is not UNSET:
            field_dict["yaraScanRule"] = yara_scan_rule
        if entire_image_scan_enabled is not UNSET:
            field_dict["entireImageScanEnabled"] = entire_image_scan_enabled
        if disk_content_validation_enabled is not UNSET:
            field_dict["diskContentValidationEnabled"] = disk_content_validation_enabled
        if notifications is not UNSET:
            field_dict["notifications"] = notifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sure_backup_job_notification_settings_model import SureBackupJobNotificationSettingsModel

        d = dict(src_dict)
        malware_scan_enabled = d.pop("malwareScanEnabled")

        yara_scan_enabled = d.pop("yaraScanEnabled")

        yara_scan_rule = d.pop("yaraScanRule", UNSET)

        entire_image_scan_enabled = d.pop("entireImageScanEnabled", UNSET)

        disk_content_validation_enabled = d.pop("diskContentValidationEnabled", UNSET)

        _notifications = d.pop("notifications", UNSET)
        notifications: SureBackupJobNotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = SureBackupJobNotificationSettingsModel.from_dict(_notifications)

        sure_backup_job_verification_options_model = cls(
            malware_scan_enabled=malware_scan_enabled,
            yara_scan_enabled=yara_scan_enabled,
            yara_scan_rule=yara_scan_rule,
            entire_image_scan_enabled=entire_image_scan_enabled,
            disk_content_validation_enabled=disk_content_validation_enabled,
            notifications=notifications,
        )

        sure_backup_job_verification_options_model.additional_properties = d
        return sure_backup_job_verification_options_model

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
