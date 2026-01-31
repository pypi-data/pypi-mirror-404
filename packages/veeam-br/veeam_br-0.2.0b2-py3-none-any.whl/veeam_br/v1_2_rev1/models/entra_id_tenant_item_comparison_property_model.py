from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantItemComparisonPropertyModel")


@_attrs_define
class EntraIdTenantItemComparisonPropertyModel:
    """
    Attributes:
        property_name (str): Property name.
        read_only (bool): If `true`, the value is read-only.
        old_value (str | Unset): Property value from the earlier restore point.
        new_value (str | Unset): Property value from the later restore point.
    """

    property_name: str
    read_only: bool
    old_value: str | Unset = UNSET
    new_value: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        property_name = self.property_name

        read_only = self.read_only

        old_value = self.old_value

        new_value = self.new_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "propertyName": property_name,
                "readOnly": read_only,
            }
        )
        if old_value is not UNSET:
            field_dict["oldValue"] = old_value
        if new_value is not UNSET:
            field_dict["newValue"] = new_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        property_name = d.pop("propertyName")

        read_only = d.pop("readOnly")

        old_value = d.pop("oldValue", UNSET)

        new_value = d.pop("newValue", UNSET)

        entra_id_tenant_item_comparison_property_model = cls(
            property_name=property_name,
            read_only=read_only,
            old_value=old_value,
            new_value=new_value,
        )

        entra_id_tenant_item_comparison_property_model.additional_properties = d
        return entra_id_tenant_item_comparison_property_model

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
