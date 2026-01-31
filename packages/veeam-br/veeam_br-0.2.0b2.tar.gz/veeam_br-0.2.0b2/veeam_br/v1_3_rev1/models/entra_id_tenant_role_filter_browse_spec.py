from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRoleFilterBrowseSpec")


@_attrs_define
class EntraIdTenantRoleFilterBrowseSpec:
    """Filtering options.

    Attributes:
        display_name (str | Unset): Role display name.
        is_built_in (bool | Unset): If `true`, the role is built-in.
        is_enabled (bool | Unset): If `true`, the role is enabled.
    """

    display_name: str | Unset = UNSET
    is_built_in: bool | Unset = UNSET
    is_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        is_built_in = self.is_built_in

        is_enabled = self.is_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if is_built_in is not UNSET:
            field_dict["isBuiltIn"] = is_built_in
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        is_built_in = d.pop("isBuiltIn", UNSET)

        is_enabled = d.pop("isEnabled", UNSET)

        entra_id_tenant_role_filter_browse_spec = cls(
            display_name=display_name,
            is_built_in=is_built_in,
            is_enabled=is_enabled,
        )

        entra_id_tenant_role_filter_browse_spec.additional_properties = d
        return entra_id_tenant_role_filter_browse_spec

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
