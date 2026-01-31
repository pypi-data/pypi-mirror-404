from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.protection_group_advanced_windows_settings_model import ProtectionGroupAdvancedWindowsSettingsModel
    from ..models.protection_group_notification_settings_model import ProtectionGroupNotificationSettingsModel


T = TypeVar("T", bound="AdvancedProtectionGroupSettingsModel")


@_attrs_define
class AdvancedProtectionGroupSettingsModel:
    """Advanced settings for the protection group.

    Attributes:
        windows_agent_settings (ProtectionGroupAdvancedWindowsSettingsModel | Unset): Advanced settings for Veeam Agent
            for Microsoft Windows machines.
        notifications (ProtectionGroupNotificationSettingsModel | Unset): Notification settings.
    """

    windows_agent_settings: ProtectionGroupAdvancedWindowsSettingsModel | Unset = UNSET
    notifications: ProtectionGroupNotificationSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        windows_agent_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.windows_agent_settings, Unset):
            windows_agent_settings = self.windows_agent_settings.to_dict()

        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if windows_agent_settings is not UNSET:
            field_dict["windowsAgentSettings"] = windows_agent_settings
        if notifications is not UNSET:
            field_dict["notifications"] = notifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.protection_group_advanced_windows_settings_model import (
            ProtectionGroupAdvancedWindowsSettingsModel,
        )
        from ..models.protection_group_notification_settings_model import ProtectionGroupNotificationSettingsModel

        d = dict(src_dict)
        _windows_agent_settings = d.pop("windowsAgentSettings", UNSET)
        windows_agent_settings: ProtectionGroupAdvancedWindowsSettingsModel | Unset
        if isinstance(_windows_agent_settings, Unset):
            windows_agent_settings = UNSET
        else:
            windows_agent_settings = ProtectionGroupAdvancedWindowsSettingsModel.from_dict(_windows_agent_settings)

        _notifications = d.pop("notifications", UNSET)
        notifications: ProtectionGroupNotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = ProtectionGroupNotificationSettingsModel.from_dict(_notifications)

        advanced_protection_group_settings_model = cls(
            windows_agent_settings=windows_agent_settings,
            notifications=notifications,
        )

        advanced_protection_group_settings_model.additional_properties = d
        return advanced_protection_group_settings_model

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
