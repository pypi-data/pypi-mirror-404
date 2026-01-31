from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SecurityAnalyzerEmailNotificationSettings")


@_attrs_define
class SecurityAnalyzerEmailNotificationSettings:
    """Custom notification settings specified for Security & Compliance Analyzer.

    Attributes:
        subject (str | Unset):
        notify_on_success (bool | Unset): If `true`, email notifications are sent when the Security & Compliance
            Analyzer session completes successfully.
        notify_on_warning (bool | Unset): If `true`, email notifications are sent when the Security & Compliance
            Analyzer session completes with a warning.
        notify_on_error (bool | Unset): If `true`, email notifications are sent when the Security & Compliance Analyzer
            session fails.
    """

    subject: str | Unset = UNSET
    notify_on_success: bool | Unset = UNSET
    notify_on_warning: bool | Unset = UNSET
    notify_on_error: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subject = self.subject

        notify_on_success = self.notify_on_success

        notify_on_warning = self.notify_on_warning

        notify_on_error = self.notify_on_error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if subject is not UNSET:
            field_dict["subject"] = subject
        if notify_on_success is not UNSET:
            field_dict["notifyOnSuccess"] = notify_on_success
        if notify_on_warning is not UNSET:
            field_dict["notifyOnWarning"] = notify_on_warning
        if notify_on_error is not UNSET:
            field_dict["notifyOnError"] = notify_on_error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subject = d.pop("subject", UNSET)

        notify_on_success = d.pop("notifyOnSuccess", UNSET)

        notify_on_warning = d.pop("notifyOnWarning", UNSET)

        notify_on_error = d.pop("notifyOnError", UNSET)

        security_analyzer_email_notification_settings = cls(
            subject=subject,
            notify_on_success=notify_on_success,
            notify_on_warning=notify_on_warning,
            notify_on_error=notify_on_error,
        )

        security_analyzer_email_notification_settings.additional_properties = d
        return security_analyzer_email_notification_settings

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
