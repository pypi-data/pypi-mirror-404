from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.i_pv_4_settings_model import IPv4SettingsModel
    from ..models.i_pv_6_settings_model import IPv6SettingsModel


T = TypeVar("T", bound="IpSettingsModel")


@_attrs_define
class IpSettingsModel:
    """IP addressing settings for the helper appliance and DNS server.

    Attributes:
        i_pv_4_settings (IPv4SettingsModel | Unset): IPv4 settings.
        i_pv_6_settings (IPv6SettingsModel | Unset): IPv6 settings.
    """

    i_pv_4_settings: IPv4SettingsModel | Unset = UNSET
    i_pv_6_settings: IPv6SettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        i_pv_4_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.i_pv_4_settings, Unset):
            i_pv_4_settings = self.i_pv_4_settings.to_dict()

        i_pv_6_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.i_pv_6_settings, Unset):
            i_pv_6_settings = self.i_pv_6_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if i_pv_4_settings is not UNSET:
            field_dict["IPv4Settings"] = i_pv_4_settings
        if i_pv_6_settings is not UNSET:
            field_dict["IPv6Settings"] = i_pv_6_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.i_pv_4_settings_model import IPv4SettingsModel
        from ..models.i_pv_6_settings_model import IPv6SettingsModel

        d = dict(src_dict)
        _i_pv_4_settings = d.pop("IPv4Settings", UNSET)
        i_pv_4_settings: IPv4SettingsModel | Unset
        if isinstance(_i_pv_4_settings, Unset):
            i_pv_4_settings = UNSET
        else:
            i_pv_4_settings = IPv4SettingsModel.from_dict(_i_pv_4_settings)

        _i_pv_6_settings = d.pop("IPv6Settings", UNSET)
        i_pv_6_settings: IPv6SettingsModel | Unset
        if isinstance(_i_pv_6_settings, Unset):
            i_pv_6_settings = UNSET
        else:
            i_pv_6_settings = IPv6SettingsModel.from_dict(_i_pv_6_settings)

        ip_settings_model = cls(
            i_pv_4_settings=i_pv_4_settings,
            i_pv_6_settings=i_pv_6_settings,
        )

        ip_settings_model.additional_properties = d
        return ip_settings_model

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
