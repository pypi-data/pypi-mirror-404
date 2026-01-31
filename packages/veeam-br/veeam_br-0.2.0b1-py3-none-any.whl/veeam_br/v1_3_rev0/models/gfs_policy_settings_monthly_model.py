from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_sennight_of_month import ESennightOfMonth
from ..types import UNSET, Unset

T = TypeVar("T", bound="GFSPolicySettingsMonthlyModel")


@_attrs_define
class GFSPolicySettingsMonthlyModel:
    """Monthly GFS retention policy.

    Attributes:
        is_enabled (bool): If `true`, the monthly GFS retention policy is enabled.
        keep_for_number_of_months (int | Unset): Number of months to keep full backups for archival purposes. Possible
            values are from 1 through 999.
        desired_time (ESennightOfMonth | Unset): Sennight of the month.
    """

    is_enabled: bool
    keep_for_number_of_months: int | Unset = UNSET
    desired_time: ESennightOfMonth | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        keep_for_number_of_months = self.keep_for_number_of_months

        desired_time: str | Unset = UNSET
        if not isinstance(self.desired_time, Unset):
            desired_time = self.desired_time.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if keep_for_number_of_months is not UNSET:
            field_dict["keepForNumberOfMonths"] = keep_for_number_of_months
        if desired_time is not UNSET:
            field_dict["desiredTime"] = desired_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        keep_for_number_of_months = d.pop("keepForNumberOfMonths", UNSET)

        _desired_time = d.pop("desiredTime", UNSET)
        desired_time: ESennightOfMonth | Unset
        if isinstance(_desired_time, Unset):
            desired_time = UNSET
        else:
            desired_time = ESennightOfMonth(_desired_time)

        gfs_policy_settings_monthly_model = cls(
            is_enabled=is_enabled,
            keep_for_number_of_months=keep_for_number_of_months,
            desired_time=desired_time,
        )

        gfs_policy_settings_monthly_model.additional_properties = d
        return gfs_policy_settings_monthly_model

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
