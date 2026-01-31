from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_mount_server_settings_type import EMountServerSettingsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_server_settings_model import MountServerSettingsModel


T = TypeVar("T", bound="MountServersSettingsModel")


@_attrs_define
class MountServersSettingsModel:
    """Mount server settings.

    Attributes:
        mount_server_settings_type (EMountServerSettingsType): Type of mount server settings.
        windows (MountServerSettingsModel | Unset): Settings for the mount server that is used for file and application
            items restore.
        linux (MountServerSettingsModel | Unset): Settings for the mount server that is used for file and application
            items restore.
    """

    mount_server_settings_type: EMountServerSettingsType
    windows: MountServerSettingsModel | Unset = UNSET
    linux: MountServerSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mount_server_settings_type = self.mount_server_settings_type.value

        windows: dict[str, Any] | Unset = UNSET
        if not isinstance(self.windows, Unset):
            windows = self.windows.to_dict()

        linux: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux, Unset):
            linux = self.linux.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mountServerSettingsType": mount_server_settings_type,
            }
        )
        if windows is not UNSET:
            field_dict["windows"] = windows
        if linux is not UNSET:
            field_dict["linux"] = linux

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_server_settings_model import MountServerSettingsModel

        d = dict(src_dict)
        mount_server_settings_type = EMountServerSettingsType(d.pop("mountServerSettingsType"))

        _windows = d.pop("windows", UNSET)
        windows: MountServerSettingsModel | Unset
        if isinstance(_windows, Unset):
            windows = UNSET
        else:
            windows = MountServerSettingsModel.from_dict(_windows)

        _linux = d.pop("linux", UNSET)
        linux: MountServerSettingsModel | Unset
        if isinstance(_linux, Unset):
            linux = UNSET
        else:
            linux = MountServerSettingsModel.from_dict(_linux)

        mount_servers_settings_model = cls(
            mount_server_settings_type=mount_server_settings_type,
            windows=windows,
            linux=linux,
        )

        mount_servers_settings_model.additional_properties = d
        return mount_servers_settings_model

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
