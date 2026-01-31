from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantBitlockerKeyFilterBrowseSpec")


@_attrs_define
class EntraIdTenantBitlockerKeyFilterBrowseSpec:
    """
    Attributes:
        key (str | Unset):
        device_id (str | Unset):
        device_display_name (str | Unset):
    """

    key: str | Unset = UNSET
    device_id: str | Unset = UNSET
    device_display_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        device_id = self.device_id

        device_display_name = self.device_display_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if device_display_name is not UNSET:
            field_dict["deviceDisplayName"] = device_display_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key", UNSET)

        device_id = d.pop("deviceId", UNSET)

        device_display_name = d.pop("deviceDisplayName", UNSET)

        entra_id_tenant_bitlocker_key_filter_browse_spec = cls(
            key=key,
            device_id=device_id,
            device_display_name=device_display_name,
        )

        entra_id_tenant_bitlocker_key_filter_browse_spec.additional_properties = d
        return entra_id_tenant_bitlocker_key_filter_browse_spec

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
