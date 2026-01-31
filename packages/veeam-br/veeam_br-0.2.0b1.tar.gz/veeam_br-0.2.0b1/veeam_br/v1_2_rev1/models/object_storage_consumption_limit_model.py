from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_consumption_limit_kind import EConsumptionLimitKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectStorageConsumptionLimitModel")


@_attrs_define
class ObjectStorageConsumptionLimitModel:
    """Soft consumption limit for the storage. The limit can be exceeded temporarily.

    Attributes:
        is_enabled (bool | Unset): If `true`, the consumption limit is enabled.
        consumption_limit_count (int | Unset): Limit value.
        consumption_limit_kind (EConsumptionLimitKind | Unset): Measurement unit.
    """

    is_enabled: bool | Unset = UNSET
    consumption_limit_count: int | Unset = UNSET
    consumption_limit_kind: EConsumptionLimitKind | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        consumption_limit_count = self.consumption_limit_count

        consumption_limit_kind: str | Unset = UNSET
        if not isinstance(self.consumption_limit_kind, Unset):
            consumption_limit_kind = self.consumption_limit_kind.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if consumption_limit_count is not UNSET:
            field_dict["consumptionLimitCount"] = consumption_limit_count
        if consumption_limit_kind is not UNSET:
            field_dict["consumptionLimitKind"] = consumption_limit_kind

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled", UNSET)

        consumption_limit_count = d.pop("consumptionLimitCount", UNSET)

        _consumption_limit_kind = d.pop("consumptionLimitKind", UNSET)
        consumption_limit_kind: EConsumptionLimitKind | Unset
        if isinstance(_consumption_limit_kind, Unset):
            consumption_limit_kind = UNSET
        else:
            consumption_limit_kind = EConsumptionLimitKind(_consumption_limit_kind)

        object_storage_consumption_limit_model = cls(
            is_enabled=is_enabled,
            consumption_limit_count=consumption_limit_count,
            consumption_limit_kind=consumption_limit_kind,
        )

        object_storage_consumption_limit_model.additional_properties = d
        return object_storage_consumption_limit_model

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
