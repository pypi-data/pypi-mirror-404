from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.advanced_smtp_options_model import AdvancedSmtpOptionsModel


T = TypeVar("T", bound="GeneralOptionsEmailNotificationsModel")


@_attrs_define
class GeneralOptionsEmailNotificationsModel:
    """Global email notification settings and job notifications.

    Attributes:
        smtp_server_name (str): Full DNS name or IP address of the SMTP server.
        advanced_smtp_options (AdvancedSmtpOptionsModel): Advanced global email notification settings.
        from_ (str): Email address from which email notifications must be sent.
        to (str): Recipient email addresses. Use a semicolon to separate multiple addresses.
        subject (str): Notification subject. Use the following variables in the subject:<ul> <li>%Time% — completion
            time</li> <li>%JobName% — job name</li> <li>%JobResult% — job result</li> <li>%ObjectCount% — number of VMs in
            the job</li> <li>%Issues% — number of VMs in the job that have been processed with the Warning or Failed
            status</li></ul>
        send_daily_reports_at (datetime.datetime): Time when Veeam Backup & Replication sends daily email reports.
        notify_on_success (bool): If `true`, email notifications are sent when the job completes successfully.
        notify_on_warning (bool): If `true`, email notifications are sent when the job completes with a warning.
        notify_on_failure (bool): If `true`, email notifications are sent when the job fails.
        notify_on_last_retry (bool): If `true`, email notifications are sent about the final job status only (not per
            every job retry).
    """

    smtp_server_name: str
    advanced_smtp_options: AdvancedSmtpOptionsModel
    from_: str
    to: str
    subject: str
    send_daily_reports_at: datetime.datetime
    notify_on_success: bool
    notify_on_warning: bool
    notify_on_failure: bool
    notify_on_last_retry: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        smtp_server_name = self.smtp_server_name

        advanced_smtp_options = self.advanced_smtp_options.to_dict()

        from_ = self.from_

        to = self.to

        subject = self.subject

        send_daily_reports_at = self.send_daily_reports_at.isoformat()

        notify_on_success = self.notify_on_success

        notify_on_warning = self.notify_on_warning

        notify_on_failure = self.notify_on_failure

        notify_on_last_retry = self.notify_on_last_retry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "smtpServerName": smtp_server_name,
                "advancedSmtpOptions": advanced_smtp_options,
                "from": from_,
                "to": to,
                "subject": subject,
                "sendDailyReportsAt": send_daily_reports_at,
                "notifyOnSuccess": notify_on_success,
                "notifyOnWarning": notify_on_warning,
                "notifyOnFailure": notify_on_failure,
                "notifyOnLastRetry": notify_on_last_retry,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.advanced_smtp_options_model import AdvancedSmtpOptionsModel

        d = dict(src_dict)
        smtp_server_name = d.pop("smtpServerName")

        advanced_smtp_options = AdvancedSmtpOptionsModel.from_dict(d.pop("advancedSmtpOptions"))

        from_ = d.pop("from")

        to = d.pop("to")

        subject = d.pop("subject")

        send_daily_reports_at = isoparse(d.pop("sendDailyReportsAt"))

        notify_on_success = d.pop("notifyOnSuccess")

        notify_on_warning = d.pop("notifyOnWarning")

        notify_on_failure = d.pop("notifyOnFailure")

        notify_on_last_retry = d.pop("notifyOnLastRetry")

        general_options_email_notifications_model = cls(
            smtp_server_name=smtp_server_name,
            advanced_smtp_options=advanced_smtp_options,
            from_=from_,
            to=to,
            subject=subject,
            send_daily_reports_at=send_daily_reports_at,
            notify_on_success=notify_on_success,
            notify_on_warning=notify_on_warning,
            notify_on_failure=notify_on_failure,
            notify_on_last_retry=notify_on_last_retry,
        )

        general_options_email_notifications_model.additional_properties = d
        return general_options_email_notifications_model

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
