from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CapacityTierOverridePolicyModel")


@_attrs_define
class CapacityTierOverridePolicyModel:
    """Policy that overrides the move policy if the scale-out backup repository reaches a certain space threshold.

    Attributes:
        is_enabled (bool): If `true`, Veeam Backup & Replication moves the oldest backup files sooner if the scale-out
            backup repository reaches the space threshold.
        override_space_threshold_percents (int | Unset): Space threshold of the scale-out backup repository, in percent.
    """

    is_enabled: bool
    override_space_threshold_percents: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        override_space_threshold_percents = self.override_space_threshold_percents

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if override_space_threshold_percents is not UNSET:
            field_dict["overrideSpaceThresholdPercents"] = override_space_threshold_percents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        override_space_threshold_percents = d.pop("overrideSpaceThresholdPercents", UNSET)

        capacity_tier_override_policy_model = cls(
            is_enabled=is_enabled,
            override_space_threshold_percents=override_space_threshold_percents,
        )

        capacity_tier_override_policy_model.additional_properties = d
        return capacity_tier_override_policy_model

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
