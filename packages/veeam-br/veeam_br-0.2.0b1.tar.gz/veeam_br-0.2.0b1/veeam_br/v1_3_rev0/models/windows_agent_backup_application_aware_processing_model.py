from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.windows_agent_backup_application_settings_model import WindowsAgentBackupApplicationSettingsModel


T = TypeVar("T", bound="WindowsAgentBackupApplicationAwareProcessingModel")


@_attrs_define
class WindowsAgentBackupApplicationAwareProcessingModel:
    """Application-aware processing settings.

    Attributes:
        is_enabled (bool): If `true`, application-aware processing is enabled.
        app_settings (list[WindowsAgentBackupApplicationSettingsModel] | Unset): Array of Windows machines and their
            application settings.
    """

    is_enabled: bool
    app_settings: list[WindowsAgentBackupApplicationSettingsModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        app_settings: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.app_settings, Unset):
            app_settings = []
            for app_settings_item_data in self.app_settings:
                app_settings_item = app_settings_item_data.to_dict()
                app_settings.append(app_settings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if app_settings is not UNSET:
            field_dict["appSettings"] = app_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.windows_agent_backup_application_settings_model import WindowsAgentBackupApplicationSettingsModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _app_settings = d.pop("appSettings", UNSET)
        app_settings: list[WindowsAgentBackupApplicationSettingsModel] | Unset = UNSET
        if _app_settings is not UNSET:
            app_settings = []
            for app_settings_item_data in _app_settings:
                app_settings_item = WindowsAgentBackupApplicationSettingsModel.from_dict(app_settings_item_data)

                app_settings.append(app_settings_item)

        windows_agent_backup_application_aware_processing_model = cls(
            is_enabled=is_enabled,
            app_settings=app_settings,
        )

        windows_agent_backup_application_aware_processing_model.additional_properties = d
        return windows_agent_backup_application_aware_processing_model

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
