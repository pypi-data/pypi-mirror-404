from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantItemRecursiveComparisonNode")


@_attrs_define
class EntraIdTenantItemRecursiveComparisonNode:
    """
    Attributes:
        are_equal (bool): If `true`, the property values are equal.
        name (str): Property name.
        path (str): Property path.
        is_read_only (bool | Unset): If `true`, the property is read only.
        old_value (str | Unset): Property value from the earlier restore point.
        new_value (str | Unset): Property value from the later restore point.
        children (list[EntraIdTenantItemRecursiveComparisonNode] | Unset): Array of child properties.
    """

    are_equal: bool
    name: str
    path: str
    is_read_only: bool | Unset = UNSET
    old_value: str | Unset = UNSET
    new_value: str | Unset = UNSET
    children: list[EntraIdTenantItemRecursiveComparisonNode] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        are_equal = self.are_equal

        name = self.name

        path = self.path

        is_read_only = self.is_read_only

        old_value = self.old_value

        new_value = self.new_value

        children: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item = children_item_data.to_dict()
                children.append(children_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "areEqual": are_equal,
                "name": name,
                "path": path,
            }
        )
        if is_read_only is not UNSET:
            field_dict["isReadOnly"] = is_read_only
        if old_value is not UNSET:
            field_dict["oldValue"] = old_value
        if new_value is not UNSET:
            field_dict["newValue"] = new_value
        if children is not UNSET:
            field_dict["children"] = children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        are_equal = d.pop("areEqual")

        name = d.pop("name")

        path = d.pop("path")

        is_read_only = d.pop("isReadOnly", UNSET)

        old_value = d.pop("oldValue", UNSET)

        new_value = d.pop("newValue", UNSET)

        _children = d.pop("children", UNSET)
        children: list[EntraIdTenantItemRecursiveComparisonNode] | Unset = UNSET
        if _children is not UNSET:
            children = []
            for children_item_data in _children:
                children_item = EntraIdTenantItemRecursiveComparisonNode.from_dict(children_item_data)

                children.append(children_item)

        entra_id_tenant_item_recursive_comparison_node = cls(
            are_equal=are_equal,
            name=name,
            path=path,
            is_read_only=is_read_only,
            old_value=old_value,
            new_value=new_value,
            children=children,
        )

        entra_id_tenant_item_recursive_comparison_node.additional_properties = d
        return entra_id_tenant_item_recursive_comparison_node

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
