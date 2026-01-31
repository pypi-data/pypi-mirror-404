from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FlrCompareToProductionSpec")


@_attrs_define
class FlrCompareToProductionSpec:
    """
    Attributes:
        is_enabled (bool): If `true`, the paths are included in the comparison. Otherwise, they are excluded from the
            comparison.
        paths (list[str]): Array of item paths that you want to compare.
    """

    is_enabled: bool
    paths: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        paths = self.paths

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
                "paths": paths,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        paths = cast(list[str], d.pop("paths"))

        flr_compare_to_production_spec = cls(
            is_enabled=is_enabled,
            paths=paths,
        )

        flr_compare_to_production_spec.additional_properties = d
        return flr_compare_to_production_spec

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
