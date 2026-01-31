from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_email_settings_server_type import EEmailSettingsServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.advanced_smtp_options_model import AdvancedSmtpOptionsModel
    from ..models.general_options_email_settings_model import GeneralOptionsEmailSettingsModel


T = TypeVar("T", bound="GeneralOptionsSMTPServerSettingsModel")


@_attrs_define
class GeneralOptionsSMTPServerSettingsModel:
    """SMTP server settings.

    Attributes:
        notifications_enabled (bool): Indicates whether the email notifications are enabled. If true, the
            `emailSettings` property is required. Default: False.
        mail_server (EEmailSettingsServerType | Unset): Type of mail server.
        email_settings (GeneralOptionsEmailSettingsModel | Unset): Email notification settings.
        smtp_server_name (str | Unset): Full DNS name or IP address of the SMTP server.
        advanced_smtp_options (AdvancedSmtpOptionsModel | Unset): Advanced global email notification settings.
    """

    notifications_enabled: bool = False
    mail_server: EEmailSettingsServerType | Unset = UNSET
    email_settings: GeneralOptionsEmailSettingsModel | Unset = UNSET
    smtp_server_name: str | Unset = UNSET
    advanced_smtp_options: AdvancedSmtpOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        notifications_enabled = self.notifications_enabled

        mail_server: str | Unset = UNSET
        if not isinstance(self.mail_server, Unset):
            mail_server = self.mail_server.value

        email_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.email_settings, Unset):
            email_settings = self.email_settings.to_dict()

        smtp_server_name = self.smtp_server_name

        advanced_smtp_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_smtp_options, Unset):
            advanced_smtp_options = self.advanced_smtp_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "notificationsEnabled": notifications_enabled,
            }
        )
        if mail_server is not UNSET:
            field_dict["mailServer"] = mail_server
        if email_settings is not UNSET:
            field_dict["emailSettings"] = email_settings
        if smtp_server_name is not UNSET:
            field_dict["smtpServerName"] = smtp_server_name
        if advanced_smtp_options is not UNSET:
            field_dict["advancedSmtpOptions"] = advanced_smtp_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.advanced_smtp_options_model import AdvancedSmtpOptionsModel
        from ..models.general_options_email_settings_model import GeneralOptionsEmailSettingsModel

        d = dict(src_dict)
        notifications_enabled = d.pop("notificationsEnabled")

        _mail_server = d.pop("mailServer", UNSET)
        mail_server: EEmailSettingsServerType | Unset
        if isinstance(_mail_server, Unset):
            mail_server = UNSET
        else:
            mail_server = EEmailSettingsServerType(_mail_server)

        _email_settings = d.pop("emailSettings", UNSET)
        email_settings: GeneralOptionsEmailSettingsModel | Unset
        if isinstance(_email_settings, Unset):
            email_settings = UNSET
        else:
            email_settings = GeneralOptionsEmailSettingsModel.from_dict(_email_settings)

        smtp_server_name = d.pop("smtpServerName", UNSET)

        _advanced_smtp_options = d.pop("advancedSmtpOptions", UNSET)
        advanced_smtp_options: AdvancedSmtpOptionsModel | Unset
        if isinstance(_advanced_smtp_options, Unset):
            advanced_smtp_options = UNSET
        else:
            advanced_smtp_options = AdvancedSmtpOptionsModel.from_dict(_advanced_smtp_options)

        general_options_smtp_server_settings_model = cls(
            notifications_enabled=notifications_enabled,
            mail_server=mail_server,
            email_settings=email_settings,
            smtp_server_name=smtp_server_name,
            advanced_smtp_options=advanced_smtp_options,
        )

        general_options_smtp_server_settings_model.additional_properties = d
        return general_options_smtp_server_settings_model

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
