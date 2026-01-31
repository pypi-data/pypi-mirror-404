from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_email_settings_server_type import EEmailSettingsServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.general_options_email_settings_model import GeneralOptionsEmailSettingsModel


T = TypeVar("T", bound="GeneralOptionsMS365ServerSettingsModel")


@_attrs_define
class GeneralOptionsMS365ServerSettingsModel:
    """Microsoft 365 server settings.

    Attributes:
        notifications_enabled (bool): Indicates whether the email notifications are enabled. If true, the
            `emailSettings` property is required. Default: False.
        mail_server (EEmailSettingsServerType | Unset): Type of mail server.
        email_settings (GeneralOptionsEmailSettingsModel | Unset): Email notification settings.
        app_client_id (str | Unset): Application client ID.
        tenant (str | Unset): Tenant ID.
    """

    notifications_enabled: bool = False
    mail_server: EEmailSettingsServerType | Unset = UNSET
    email_settings: GeneralOptionsEmailSettingsModel | Unset = UNSET
    app_client_id: str | Unset = UNSET
    tenant: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        notifications_enabled = self.notifications_enabled

        mail_server: str | Unset = UNSET
        if not isinstance(self.mail_server, Unset):
            mail_server = self.mail_server.value

        email_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.email_settings, Unset):
            email_settings = self.email_settings.to_dict()

        app_client_id = self.app_client_id

        tenant = self.tenant

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
        if app_client_id is not UNSET:
            field_dict["appClientId"] = app_client_id
        if tenant is not UNSET:
            field_dict["tenant"] = tenant

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        app_client_id = d.pop("appClientId", UNSET)

        tenant = d.pop("tenant", UNSET)

        general_options_ms365_server_settings_model = cls(
            notifications_enabled=notifications_enabled,
            mail_server=mail_server,
            email_settings=email_settings,
            app_client_id=app_client_id,
            tenant=tenant,
        )

        general_options_ms365_server_settings_model.additional_properties = d
        return general_options_ms365_server_settings_model

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
