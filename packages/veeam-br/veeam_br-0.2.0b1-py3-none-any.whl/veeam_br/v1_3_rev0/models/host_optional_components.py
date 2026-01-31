from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.optional_component_model import OptionalComponentModel


T = TypeVar("T", bound="HostOptionalComponents")


@_attrs_define
class HostOptionalComponents:
    """Optional components to be installed on the server.

    Attributes:
        optional_components (list[OptionalComponentModel]): Array of optional components.
    """

    optional_components: list[OptionalComponentModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        optional_components = []
        for optional_components_item_data in self.optional_components:
            optional_components_item = optional_components_item_data.to_dict()
            optional_components.append(optional_components_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "optionalComponents": optional_components,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.optional_component_model import OptionalComponentModel

        d = dict(src_dict)
        optional_components = []
        _optional_components = d.pop("optionalComponents")
        for optional_components_item_data in _optional_components:
            optional_components_item = OptionalComponentModel.from_dict(optional_components_item_data)

            optional_components.append(optional_components_item)

        host_optional_components = cls(
            optional_components=optional_components,
        )

        host_optional_components.additional_properties = d
        return host_optional_components

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
