from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdTenantItemComparisonReferenceValueModel")


@_attrs_define
class EntraIdTenantItemComparisonReferenceValueModel:
    """Reference value.

    Attributes:
        display_name (str): Reference display name.
        reference_id (str): Reference ID.
        old_value (bool): Value from the earlier restore point.
        new_value (bool): Value from the newer restore point.
    """

    display_name: str
    reference_id: str
    old_value: bool
    new_value: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        reference_id = self.reference_id

        old_value = self.old_value

        new_value = self.new_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "displayName": display_name,
                "referenceId": reference_id,
                "oldValue": old_value,
                "newValue": new_value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName")

        reference_id = d.pop("referenceId")

        old_value = d.pop("oldValue")

        new_value = d.pop("newValue")

        entra_id_tenant_item_comparison_reference_value_model = cls(
            display_name=display_name,
            reference_id=reference_id,
            old_value=old_value,
            new_value=new_value,
        )

        entra_id_tenant_item_comparison_reference_value_model.additional_properties = d
        return entra_id_tenant_item_comparison_reference_value_model

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
