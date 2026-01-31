from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_immutability_mode import ERepositoryImmutabilityMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectStorageImmutabilityModel")


@_attrs_define
class ObjectStorageImmutabilityModel:
    """Object storage immutability.

    Attributes:
        is_enabled (bool | Unset): If `true`, immutability is enabled.
        days_count (int | Unset): Immutability period, in days.
        immutability_mode (ERepositoryImmutabilityMode | Unset): Repository immutability mode.
    """

    is_enabled: bool | Unset = UNSET
    days_count: int | Unset = UNSET
    immutability_mode: ERepositoryImmutabilityMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        days_count = self.days_count

        immutability_mode: str | Unset = UNSET
        if not isinstance(self.immutability_mode, Unset):
            immutability_mode = self.immutability_mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if days_count is not UNSET:
            field_dict["daysCount"] = days_count
        if immutability_mode is not UNSET:
            field_dict["immutabilityMode"] = immutability_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled", UNSET)

        days_count = d.pop("daysCount", UNSET)

        _immutability_mode = d.pop("immutabilityMode", UNSET)
        immutability_mode: ERepositoryImmutabilityMode | Unset
        if isinstance(_immutability_mode, Unset):
            immutability_mode = UNSET
        else:
            immutability_mode = ERepositoryImmutabilityMode(_immutability_mode)

        object_storage_immutability_model = cls(
            is_enabled=is_enabled,
            days_count=days_count,
            immutability_mode=immutability_mode,
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
