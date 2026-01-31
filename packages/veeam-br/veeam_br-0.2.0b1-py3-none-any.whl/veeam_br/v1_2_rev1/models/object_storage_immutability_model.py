from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectStorageImmutabilityModel")


@_attrs_define
class ObjectStorageImmutabilityModel:
    """Object storage immutability.

    Attributes:
        is_enabled (bool | Unset): If `true`, storage immutability is enabled.
        days_count (int | Unset): Immutability period.
    """

    is_enabled: bool | Unset = UNSET
    days_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        days_count = self.days_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if days_count is not UNSET:
            field_dict["daysCount"] = days_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled", UNSET)

        days_count = d.pop("daysCount", UNSET)

        object_storage_immutability_model = cls(
            is_enabled=is_enabled,
            days_count=days_count,
        )

        object_storage_immutability_model.additional_properties = d
        return object_storage_immutability_model

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
