from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.flr_compare_attribute_model import FlrCompareAttributeModel


T = TypeVar("T", bound="FlrCompareAttributesModel")


@_attrs_define
class FlrCompareAttributesModel:
    """
    Attributes:
        path (str): Path of the item.
        attributes (list[FlrCompareAttributeModel]): Array of item attributes.
    """

    path: str
    attributes: list[FlrCompareAttributeModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        attributes = []
        for attributes_item_data in self.attributes:
            attributes_item = attributes_item_data.to_dict()
            attributes.append(attributes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_compare_attribute_model import FlrCompareAttributeModel

        d = dict(src_dict)
        path = d.pop("path")

        attributes = []
        _attributes = d.pop("attributes")
        for attributes_item_data in _attributes:
            attributes_item = FlrCompareAttributeModel.from_dict(attributes_item_data)

            attributes.append(attributes_item)

        flr_compare_attributes_model = cls(
            path=path,
            attributes=attributes,
        )

        flr_compare_attributes_model.additional_properties = d
        return flr_compare_attributes_model

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
