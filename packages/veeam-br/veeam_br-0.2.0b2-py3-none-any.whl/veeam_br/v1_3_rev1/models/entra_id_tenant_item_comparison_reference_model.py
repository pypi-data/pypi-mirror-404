from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.entra_id_tenant_item_comparison_reference_value_model import (
        EntraIdTenantItemComparisonReferenceValueModel,
    )


T = TypeVar("T", bound="EntraIdTenantItemComparisonReferenceModel")


@_attrs_define
class EntraIdTenantItemComparisonReferenceModel:
    """Item reference (relationship with other items).

    Attributes:
        reference_type (str): Reference type.
        reference_type_display_name (str): Display name of the reference type.
        values (list[EntraIdTenantItemComparisonReferenceValueModel]): Array of values.
    """

    reference_type: str
    reference_type_display_name: str
    values: list[EntraIdTenantItemComparisonReferenceValueModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reference_type = self.reference_type

        reference_type_display_name = self.reference_type_display_name

        values = []
        for values_item_data in self.values:
            values_item = values_item_data.to_dict()
            values.append(values_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "referenceType": reference_type,
                "referenceTypeDisplayName": reference_type_display_name,
                "values": values,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_item_comparison_reference_value_model import (
            EntraIdTenantItemComparisonReferenceValueModel,
        )

        d = dict(src_dict)
        reference_type = d.pop("referenceType")

        reference_type_display_name = d.pop("referenceTypeDisplayName")

        values = []
        _values = d.pop("values")
        for values_item_data in _values:
            values_item = EntraIdTenantItemComparisonReferenceValueModel.from_dict(values_item_data)

            values.append(values_item)

        entra_id_tenant_item_comparison_reference_model = cls(
            reference_type=reference_type,
            reference_type_display_name=reference_type_display_name,
            values=values,
        )

        entra_id_tenant_item_comparison_reference_model.additional_properties = d
        return entra_id_tenant_item_comparison_reference_model

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
