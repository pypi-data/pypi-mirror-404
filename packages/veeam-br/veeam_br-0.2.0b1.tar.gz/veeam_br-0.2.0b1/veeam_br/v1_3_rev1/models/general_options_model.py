from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.general_options_email_notifications_model import GeneralOptionsEmailNotificationsModel
    from ..models.general_options_notifications_model import GeneralOptionsNotificationsModel
    from ..models.general_options_siem_integration_model import GeneralOptionsSiemIntegrationModel


T = TypeVar("T", bound="GeneralOptionsModel")


@_attrs_define
class GeneralOptionsModel:
    """Veeam Backup & Replication settings.

    Attributes:
        notification_enabled (bool): If `true`, email notifications are enabled. In this case, the `emailSettings`
            property is required. Default: False.
        notifications (GeneralOptionsNotificationsModel): Other notifications such as notifications on low disk space,
            support contract expiration, and available updates.
        siem_integration (GeneralOptionsSiemIntegrationModel): SIEM integration settings.
        email_settings (GeneralOptionsEmailNotificationsModel | Unset): Global email notification settings and job
            notifications.
    """

    notifications: GeneralOptionsNotificationsModel
    siem_integration: GeneralOptionsSiemIntegrationModel
    notification_enabled: bool = False
    email_settings: GeneralOptionsEmailNotificationsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        notification_enabled = self.notification_enabled

        notifications = self.notifications.to_dict()

        siem_integration = self.siem_integration.to_dict()

        email_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.email_settings, Unset):
            email_settings = self.email_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "notificationEnabled": notification_enabled,
                "notifications": notifications,
                "siemIntegration": siem_integration,
            }
        )
        if email_settings is not UNSET:
            field_dict["emailSettings"] = email_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.general_options_email_notifications_model import GeneralOptionsEmailNotificationsModel
        from ..models.general_options_notifications_model import GeneralOptionsNotificationsModel
        from ..models.general_options_siem_integration_model import GeneralOptionsSiemIntegrationModel

        d = dict(src_dict)
        notification_enabled = d.pop("notificationEnabled")

        notifications = GeneralOptionsNotificationsModel.from_dict(d.pop("notifications"))

        siem_integration = GeneralOptionsSiemIntegrationModel.from_dict(d.pop("siemIntegration"))

        _email_settings = d.pop("emailSettings", UNSET)
        email_settings: GeneralOptionsEmailNotificationsModel | Unset
        if isinstance(_email_settings, Unset):
            email_settings = UNSET
        else:
            email_settings = GeneralOptionsEmailNotificationsModel.from_dict(_email_settings)

        general_options_model = cls(
            notification_enabled=notification_enabled,
            notifications=notifications,
            siem_integration=siem_integration,
            email_settings=email_settings,
        )

        general_options_model.additional_properties = d
        return general_options_model

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
