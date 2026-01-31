from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.email_notification_settings_backup_copy_model import EmailNotificationSettingsBackupCopyModel


T = TypeVar("T", bound="BackupCopyJobNotificationSettingsModel")


@_attrs_define
class BackupCopyJobNotificationSettingsModel:
    """Notification settings.

    Attributes:
        send_snmp_notifications (bool | Unset): If `true`, SNMP notifications are enabled for this job.
        email_notifications (EmailNotificationSettingsBackupCopyModel | Unset): Email notification settings for the job.
    """

    send_snmp_notifications: bool | Unset = UNSET
    email_notifications: EmailNotificationSettingsBackupCopyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        send_snmp_notifications = self.send_snmp_notifications

        email_notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.email_notifications, Unset):
            email_notifications = self.email_notifications.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if send_snmp_notifications is not UNSET:
            field_dict["sendSNMPNotifications"] = send_snmp_notifications
        if email_notifications is not UNSET:
            field_dict["emailNotifications"] = email_notifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.email_notification_settings_backup_copy_model import EmailNotificationSettingsBackupCopyModel

        d = dict(src_dict)
        send_snmp_notifications = d.pop("sendSNMPNotifications", UNSET)

        _email_notifications = d.pop("emailNotifications", UNSET)
        email_notifications: EmailNotificationSettingsBackupCopyModel | Unset
        if isinstance(_email_notifications, Unset):
            email_notifications = UNSET
        else:
            email_notifications = EmailNotificationSettingsBackupCopyModel.from_dict(_email_notifications)

        backup_copy_job_notification_settings_model = cls(
            send_snmp_notifications=send_snmp_notifications,
            email_notifications=email_notifications,
        )

        backup_copy_job_notification_settings_model.additional_properties = d
        return backup_copy_job_notification_settings_model

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
