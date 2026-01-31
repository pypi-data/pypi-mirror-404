from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VPowerNFSPortSettingsModel")


@_attrs_define
class VPowerNFSPortSettingsModel:
    """Network ports used by the vPower NFS Service.

    Attributes:
        mount_port (int | Unset): Mount port.
        v_power_nfs_port (int | Unset): vPower NFS port.
    """

    mount_port: int | Unset = UNSET
    v_power_nfs_port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mount_port = self.mount_port

        v_power_nfs_port = self.v_power_nfs_port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mount_port is not UNSET:
            field_dict["mountPort"] = mount_port
        if v_power_nfs_port is not UNSET:
            field_dict["vPowerNFSPort"] = v_power_nfs_port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mount_port = d.pop("mountPort", UNSET)

        v_power_nfs_port = d.pop("vPowerNFSPort", UNSET)

        v_power_nfs_port_settings_model = cls(
            mount_port=mount_port,
            v_power_nfs_port=v_power_nfs_port,
        )

        v_power_nfs_port_settings_model.additional_properties = d
        return v_power_nfs_port_settings_model

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
