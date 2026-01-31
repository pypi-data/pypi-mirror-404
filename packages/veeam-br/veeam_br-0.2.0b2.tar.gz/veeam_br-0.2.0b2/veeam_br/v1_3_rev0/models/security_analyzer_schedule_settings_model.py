from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_email_notification_type import EEmailNotificationType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.security_analyzer_email_notification_settings import SecurityAnalyzerEmailNotificationSettings


T = TypeVar("T", bound="SecurityAnalyzerScheduleSettingsModel")


@_attrs_define
class SecurityAnalyzerScheduleSettingsModel:
    """Settings for Security & Compliance Analyzer.

    Attributes:
        daily_scan_enabled (bool | Unset): If `true`, Security & Compliance Analyzer runs daily.
        daily_scan_local_time (str | Unset): Local time when the Security & Compliance Analyzer session must start.
        send_scan_results (bool | Unset): If `true`, email notifications with scan results are enabled.
        recipients (str | Unset): Recipient email addresses separated with a semicolon.
        notification_type (EEmailNotificationType | Unset): Type of email notification settings (global notification
            settings specified for the backup server, or custom notification settings specified for this job).
        custom_notification_settings (SecurityAnalyzerEmailNotificationSettings | Unset): Custom notification settings
            specified for Security & Compliance Analyzer.
    """

    daily_scan_enabled: bool | Unset = UNSET
    daily_scan_local_time: str | Unset = UNSET
    send_scan_results: bool | Unset = UNSET
    recipients: str | Unset = UNSET
    notification_type: EEmailNotificationType | Unset = UNSET
    custom_notification_settings: SecurityAnalyzerEmailNotificationSettings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        daily_scan_enabled = self.daily_scan_enabled

        daily_scan_local_time = self.daily_scan_local_time

        send_scan_results = self.send_scan_results

        recipients = self.recipients

        notification_type: str | Unset = UNSET
        if not isinstance(self.notification_type, Unset):
            notification_type = self.notification_type.value

        custom_notification_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_notification_settings, Unset):
            custom_notification_settings = self.custom_notification_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if daily_scan_enabled is not UNSET:
            field_dict["dailyScanEnabled"] = daily_scan_enabled
        if daily_scan_local_time is not UNSET:
            field_dict["dailyScanLocalTime"] = daily_scan_local_time
        if send_scan_results is not UNSET:
            field_dict["sendScanResults"] = send_scan_results
        if recipients is not UNSET:
            field_dict["recipients"] = recipients
        if notification_type is not UNSET:
            field_dict["notificationType"] = notification_type
        if custom_notification_settings is not UNSET:
            field_dict["customNotificationSettings"] = custom_notification_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.security_analyzer_email_notification_settings import SecurityAnalyzerEmailNotificationSettings

        d = dict(src_dict)
        daily_scan_enabled = d.pop("dailyScanEnabled", UNSET)

        daily_scan_local_time = d.pop("dailyScanLocalTime", UNSET)

        send_scan_results = d.pop("sendScanResults", UNSET)

        recipients = d.pop("recipients", UNSET)

        _notification_type = d.pop("notificationType", UNSET)
        notification_type: EEmailNotificationType | Unset
        if isinstance(_notification_type, Unset):
            notification_type = UNSET
        else:
            notification_type = EEmailNotificationType(_notification_type)

        _custom_notification_settings = d.pop("customNotificationSettings", UNSET)
        custom_notification_settings: SecurityAnalyzerEmailNotificationSettings | Unset
        if isinstance(_custom_notification_settings, Unset):
            custom_notification_settings = UNSET
        else:
            custom_notification_settings = SecurityAnalyzerEmailNotificationSettings.from_dict(
                _custom_notification_settings
            )

        security_analyzer_schedule_settings_model = cls(
            daily_scan_enabled=daily_scan_enabled,
            daily_scan_local_time=daily_scan_local_time,
            send_scan_results=send_scan_results,
            recipients=recipients,
            notification_type=notification_type,
            custom_notification_settings=custom_notification_settings,
        )

        security_analyzer_schedule_settings_model.additional_properties = d
        return security_analyzer_schedule_settings_model

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
