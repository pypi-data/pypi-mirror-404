from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_config_backup_smtp_settings_type import EConfigBackupSMTPSettingsType

T = TypeVar("T", bound="ConfigBackupSMTPSettigsModel")


@_attrs_define
class ConfigBackupSMTPSettigsModel:
    """Email notification settings.

    Attributes:
        is_enabled (bool): If `true`, email notifications are enabled for this job.
        recipients (list[str]): Array of recipient email addresses.
        settings_type (EConfigBackupSMTPSettingsType): Type of notification settings.
        subject (str): Notification subject. Use the following variables in the subject:<ul> <li>*%Time%* — completion
            time</li> <li>*%JobName%* — job name</li> <li>*%JobResult%* — job result</li></ul>
        notify_on_success (bool): If `true`, email notifications are sent when the job completes successfully.
        notify_on_warning (bool): If `true`, email notifications are sent when the job completes with a warning.
        notify_on_error (bool): If `true`, email notifications are sent when the job fails.
    """

    is_enabled: bool
    recipients: list[str]
    settings_type: EConfigBackupSMTPSettingsType
    subject: str
    notify_on_success: bool
    notify_on_warning: bool
    notify_on_error: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        recipients = self.recipients

        settings_type = self.settings_type.value

        subject = self.subject

        notify_on_success = self.notify_on_success

        notify_on_warning = self.notify_on_warning

        notify_on_error = self.notify_on_error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
                "recipients": recipients,
                "settingsType": settings_type,
                "subject": subject,
                "notifyOnSuccess": notify_on_success,
                "notifyOnWarning": notify_on_warning,
                "notifyOnError": notify_on_error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        recipients = cast(list[str], d.pop("recipients"))

        settings_type = EConfigBackupSMTPSettingsType(d.pop("settingsType"))

        subject = d.pop("subject")

        notify_on_success = d.pop("notifyOnSuccess")

        notify_on_warning = d.pop("notifyOnWarning")

        notify_on_error = d.pop("notifyOnError")

        config_backup_smtp_settigs_model = cls(
            is_enabled=is_enabled,
            recipients=recipients,
            settings_type=settings_type,
            subject=subject,
            notify_on_success=notify_on_success,
            notify_on_warning=notify_on_warning,
            notify_on_error=notify_on_error,
        )

        config_backup_smtp_settigs_model.additional_properties = d
        return config_backup_smtp_settigs_model

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
