from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_email_notification_schedule import EEmailNotificationSchedule
from ..models.e_email_notification_type import EEmailNotificationType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.email_custom_notification_type import EmailCustomNotificationType


T = TypeVar("T", bound="EmailNotificationSettingsBackupCopyModel")


@_attrs_define
class EmailNotificationSettingsBackupCopyModel:
    """Email notification settings for the job.

    Attributes:
        is_enabled (bool): If `true`, email notifications are enabled for this job.
        recipients (list[str] | Unset): Array of recipient email addresses.
        daily_report_summarylocal_time (str | Unset): Time when daily report summary is sent.
        notification_type (EEmailNotificationType | Unset): Type of email notification settings (global notification
            settings specified for the backup server, or custom notification settings specified for this job).
        custom_notification_settings (EmailCustomNotificationType | Unset): Custom notification settings.
        notifications_schedule (EEmailNotificationSchedule | Unset): For the immediate copy mode - settings for email
            notifications schedule.
    """

    is_enabled: bool
    recipients: list[str] | Unset = UNSET
    daily_report_summarylocal_time: str | Unset = UNSET
    notification_type: EEmailNotificationType | Unset = UNSET
    custom_notification_settings: EmailCustomNotificationType | Unset = UNSET
    notifications_schedule: EEmailNotificationSchedule | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        recipients: list[str] | Unset = UNSET
        if not isinstance(self.recipients, Unset):
            recipients = self.recipients

        daily_report_summarylocal_time = self.daily_report_summarylocal_time

        notification_type: str | Unset = UNSET
        if not isinstance(self.notification_type, Unset):
            notification_type = self.notification_type.value

        custom_notification_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_notification_settings, Unset):
            custom_notification_settings = self.custom_notification_settings.to_dict()

        notifications_schedule: str | Unset = UNSET
        if not isinstance(self.notifications_schedule, Unset):
            notifications_schedule = self.notifications_schedule.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if recipients is not UNSET:
            field_dict["recipients"] = recipients
        if daily_report_summarylocal_time is not UNSET:
            field_dict["dailyReportSummarylocalTime"] = daily_report_summarylocal_time
        if notification_type is not UNSET:
            field_dict["notificationType"] = notification_type
        if custom_notification_settings is not UNSET:
            field_dict["customNotificationSettings"] = custom_notification_settings
        if notifications_schedule is not UNSET:
            field_dict["notificationsSchedule"] = notifications_schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.email_custom_notification_type import EmailCustomNotificationType

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        recipients = cast(list[str], d.pop("recipients", UNSET))

        daily_report_summarylocal_time = d.pop("dailyReportSummarylocalTime", UNSET)

        _notification_type = d.pop("notificationType", UNSET)
        notification_type: EEmailNotificationType | Unset
        if isinstance(_notification_type, Unset):
            notification_type = UNSET
        else:
            notification_type = EEmailNotificationType(_notification_type)

        _custom_notification_settings = d.pop("customNotificationSettings", UNSET)
        custom_notification_settings: EmailCustomNotificationType | Unset
        if isinstance(_custom_notification_settings, Unset):
            custom_notification_settings = UNSET
        else:
            custom_notification_settings = EmailCustomNotificationType.from_dict(_custom_notification_settings)

        _notifications_schedule = d.pop("notificationsSchedule", UNSET)
        notifications_schedule: EEmailNotificationSchedule | Unset
        if isinstance(_notifications_schedule, Unset):
            notifications_schedule = UNSET
        else:
            notifications_schedule = EEmailNotificationSchedule(_notifications_schedule)

        email_notification_settings_backup_copy_model = cls(
            is_enabled=is_enabled,
            recipients=recipients,
            daily_report_summarylocal_time=daily_report_summarylocal_time,
            notification_type=notification_type,
            custom_notification_settings=custom_notification_settings,
            notifications_schedule=notifications_schedule,
        )

        email_notification_settings_backup_copy_model.additional_properties = d
        return email_notification_settings_backup_copy_model

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
