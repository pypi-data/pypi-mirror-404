from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_saved_tenant_item_type import EEntraIdSavedTenantItemType
from ..models.e_entra_id_tenant_item_change_type import EEntraIDTenantItemChangeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RestorePointChangeModel")


@_attrs_define
class RestorePointChangeModel:
    """Restore point changes.

    Attributes:
        item_type (EEntraIdSavedTenantItemType | Unset): Item type.
        change_type (EEntraIDTenantItemChangeType | Unset): Change type.
        counter (int | Unset): Number of changed items.
    """

    item_type: EEntraIdSavedTenantItemType | Unset = UNSET
    change_type: EEntraIDTenantItemChangeType | Unset = UNSET
    counter: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_type: str | Unset = UNSET
        if not isinstance(self.item_type, Unset):
            item_type = self.item_type.value

        change_type: str | Unset = UNSET
        if not isinstance(self.change_type, Unset):
            change_type = self.change_type.value

        counter = self.counter

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if item_type is not UNSET:
            field_dict["itemType"] = item_type
        if change_type is not UNSET:
            field_dict["changeType"] = change_type
        if counter is not UNSET:
            field_dict["counter"] = counter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _item_type = d.pop("itemType", UNSET)
        item_type: EEntraIdSavedTenantItemType | Unset
        if isinstance(_item_type, Unset):
            item_type = UNSET
        else:
            item_type = EEntraIdSavedTenantItemType(_item_type)

        _change_type = d.pop("changeType", UNSET)
        change_type: EEntraIDTenantItemChangeType | Unset
        if isinstance(_change_type, Unset):
            change_type = UNSET
        else:
            change_type = EEntraIDTenantItemChangeType(_change_type)

        counter = d.pop("counter", UNSET)

        restore_point_change_model = cls(
            item_type=item_type,
            change_type=change_type,
            counter=counter,
        )

        restore_point_change_model.additional_properties = d
        return restore_point_change_model

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
