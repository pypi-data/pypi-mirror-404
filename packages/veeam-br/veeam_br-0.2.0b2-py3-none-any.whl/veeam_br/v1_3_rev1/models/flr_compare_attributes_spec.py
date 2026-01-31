from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrCompareAttributesSpec")


@_attrs_define
class FlrCompareAttributesSpec:
    """Settings for comparing item attributes.

    Attributes:
        path (str): Path to the item whose attributes you want to compare.
        show_unchanged_attributes (bool | Unset): If `true`, unchanged item attributes are also returned.
    """

    path: str
    show_unchanged_attributes: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        show_unchanged_attributes = self.show_unchanged_attributes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
            }
        )
        if show_unchanged_attributes is not UNSET:
            field_dict["showUnchangedAttributes"] = show_unchanged_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        show_unchanged_attributes = d.pop("showUnchangedAttributes", UNSET)

        flr_compare_attributes_spec = cls(
            path=path,
            show_unchanged_attributes=show_unchanged_attributes,
        )

        flr_compare_attributes_spec.additional_properties = d
        return flr_compare_attributes_spec

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
