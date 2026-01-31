from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_agent_backup_application_settings_model import LinuxAgentBackupApplicationSettingsModel


T = TypeVar("T", bound="LinuxAgentBackupApplicationAwareProcessingModel")


@_attrs_define
class LinuxAgentBackupApplicationAwareProcessingModel:
    """Application-aware processing settings for a protected Linux machine.

    Attributes:
        is_enabled (bool | Unset): If `true`, application-aware processing is enabled.
        app_settings (list[LinuxAgentBackupApplicationSettingsModel] | Unset): Array of protected Linux machines and
            their application-aware processing settings.
    """

    is_enabled: bool | Unset = UNSET
    app_settings: list[LinuxAgentBackupApplicationSettingsModel] | Unset = UNSET
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
        field_dict.update({})
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if app_settings is not UNSET:
            field_dict["appSettings"] = app_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_agent_backup_application_settings_model import LinuxAgentBackupApplicationSettingsModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled", UNSET)

        _app_settings = d.pop("appSettings", UNSET)
        app_settings: list[LinuxAgentBackupApplicationSettingsModel] | Unset = UNSET
        if _app_settings is not UNSET:
            app_settings = []
            for app_settings_item_data in _app_settings:
                app_settings_item = LinuxAgentBackupApplicationSettingsModel.from_dict(app_settings_item_data)

                app_settings.append(app_settings_item)

        linux_agent_backup_application_aware_processing_model = cls(
            is_enabled=is_enabled,
            app_settings=app_settings,
        )

        linux_agent_backup_application_aware_processing_model.additional_properties = d
        return linux_agent_backup_application_aware_processing_model

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
