from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_group_membership_type import EEntraIdTenantGroupMembershipType
from ..models.e_entra_id_tenant_group_type import EEntraIdTenantGroupType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantGroupFilterBrowseSpec")


@_attrs_define
class EntraIdTenantGroupFilterBrowseSpec:
    """Filtering options.

    Attributes:
        display_name (str | Unset): Group display name.
        group_types (list[EEntraIdTenantGroupType] | Unset): Array of group types.
        membership_types (list[EEntraIdTenantGroupMembershipType] | Unset): Array of group membership types.
    """

    display_name: str | Unset = UNSET
    group_types: list[EEntraIdTenantGroupType] | Unset = UNSET
    membership_types: list[EEntraIdTenantGroupMembershipType] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        group_types: list[str] | Unset = UNSET
        if not isinstance(self.group_types, Unset):
            group_types = []
            for group_types_item_data in self.group_types:
                group_types_item = group_types_item_data.value
                group_types.append(group_types_item)

        membership_types: list[str] | Unset = UNSET
        if not isinstance(self.membership_types, Unset):
            membership_types = []
            for membership_types_item_data in self.membership_types:
                membership_types_item = membership_types_item_data.value
                membership_types.append(membership_types_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if group_types is not UNSET:
            field_dict["groupTypes"] = group_types
        if membership_types is not UNSET:
            field_dict["membershipTypes"] = membership_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        _group_types = d.pop("groupTypes", UNSET)
        group_types: list[EEntraIdTenantGroupType] | Unset = UNSET
        if _group_types is not UNSET:
            group_types = []
            for group_types_item_data in _group_types:
                group_types_item = EEntraIdTenantGroupType(group_types_item_data)

                group_types.append(group_types_item)

        _membership_types = d.pop("membershipTypes", UNSET)
        membership_types: list[EEntraIdTenantGroupMembershipType] | Unset = UNSET
        if _membership_types is not UNSET:
            membership_types = []
            for membership_types_item_data in _membership_types:
                membership_types_item = EEntraIdTenantGroupMembershipType(membership_types_item_data)

                membership_types.append(membership_types_item)

        entra_id_tenant_group_filter_browse_spec = cls(
            display_name=display_name,
            group_types=group_types,
            membership_types=membership_types,
        )

        entra_id_tenant_group_filter_browse_spec.additional_properties = d
        return entra_id_tenant_group_filter_browse_spec

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
