from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_application_type import EEntraIdTenantApplicationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantApplicationFilterBrowseSpec")


@_attrs_define
class EntraIdTenantApplicationFilterBrowseSpec:
    """
    Attributes:
        display_name (str | Unset):
        included_types (list[EEntraIdTenantApplicationType] | Unset):
    """

    display_name: str | Unset = UNSET
    included_types: list[EEntraIdTenantApplicationType] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        included_types: list[str] | Unset = UNSET
        if not isinstance(self.included_types, Unset):
            included_types = []
            for included_types_item_data in self.included_types:
                included_types_item = included_types_item_data.value
                included_types.append(included_types_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if included_types is not UNSET:
            field_dict["includedTypes"] = included_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        _included_types = d.pop("includedTypes", UNSET)
        included_types: list[EEntraIdTenantApplicationType] | Unset = UNSET
        if _included_types is not UNSET:
            included_types = []
            for included_types_item_data in _included_types:
                included_types_item = EEntraIdTenantApplicationType(included_types_item_data)

                included_types.append(included_types_item)

        entra_id_tenant_application_filter_browse_spec = cls(
            display_name=display_name,
            included_types=included_types,
        )

        entra_id_tenant_application_filter_browse_spec.additional_properties = d
        return entra_id_tenant_application_filter_browse_spec

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
