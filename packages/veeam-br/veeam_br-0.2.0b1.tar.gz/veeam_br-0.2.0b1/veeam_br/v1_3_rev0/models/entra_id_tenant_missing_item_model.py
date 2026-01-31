from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantMissingItemModel")


@_attrs_define
class EntraIdTenantMissingItemModel:
    """Missing Microsoft Entra ID item.

    Attributes:
        item_id (str): Item ID.
        display_name (str | Unset): Item display name.
        item_type (EEntraIdTenantItemType | Unset): Item type.
    """

    item_id: str
    display_name: str | Unset = UNSET
    item_type: EEntraIdTenantItemType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_id = self.item_id

        display_name = self.display_name

        item_type: str | Unset = UNSET
        if not isinstance(self.item_type, Unset):
            item_type = self.item_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "itemId": item_id,
            }
        )
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if item_type is not UNSET:
            field_dict["itemType"] = item_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_id = d.pop("itemId")

        display_name = d.pop("displayName", UNSET)

        _item_type = d.pop("itemType", UNSET)
        item_type: EEntraIdTenantItemType | Unset
        if isinstance(_item_type, Unset):
            item_type = UNSET
        else:
            item_type = EEntraIdTenantItemType(_item_type)

        entra_id_tenant_missing_item_model = cls(
            item_id=item_id,
            display_name=display_name,
            item_type=item_type,
        )

        entra_id_tenant_missing_item_model.additional_properties = d
        return entra_id_tenant_missing_item_model

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
