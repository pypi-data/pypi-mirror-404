from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_optional_component_type import EOptionalComponentType

T = TypeVar("T", bound="OptionalComponentModel")


@_attrs_define
class OptionalComponentModel:
    """Optional component.

    Attributes:
        display_name (str): Display name for the optional component.
        optional_component (EOptionalComponentType): Optional component type.
    """

    display_name: str
    optional_component: EOptionalComponentType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        optional_component = self.optional_component.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "displayName": display_name,
                "optionalComponent": optional_component,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName")

        optional_component = EOptionalComponentType(d.pop("optionalComponent"))

        optional_component_model = cls(
            display_name=display_name,
            optional_component=optional_component,
        )

        optional_component_model.additional_properties = d
        return optional_component_model

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
