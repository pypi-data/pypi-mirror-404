from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_day_of_week import EDayOfWeek
from ..types import UNSET, Unset

T = TypeVar("T", bound="AdvancedStorageScheduleWeeklyModel")


@_attrs_define
class AdvancedStorageScheduleWeeklyModel:
    """Weekly schedule settings.

    Attributes:
        is_enabled (bool): If `true`, the weekly schedule is enabled. Default: False.
        days (list[EDayOfWeek] | Unset): Days of the week when the operation is performed.
        local_time (str | Unset): Time when the operation is performed.
    """

    is_enabled: bool = False
    days: list[EDayOfWeek] | Unset = UNSET
    local_time: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        days: list[str] | Unset = UNSET
        if not isinstance(self.days, Unset):
            days = []
            for days_item_data in self.days:
                days_item = days_item_data.value
                days.append(days_item)

        local_time = self.local_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if days is not UNSET:
            field_dict["days"] = days
        if local_time is not UNSET:
            field_dict["localTime"] = local_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _days = d.pop("days", UNSET)
        days: list[EDayOfWeek] | Unset = UNSET
        if _days is not UNSET:
            days = []
            for days_item_data in _days:
                days_item = EDayOfWeek(days_item_data)

                days.append(days_item)

        local_time = d.pop("localTime", UNSET)

        advanced_storage_schedule_weekly_model = cls(
            is_enabled=is_enabled,
            days=days,
            local_time=local_time,
        )

        advanced_storage_schedule_weekly_model.additional_properties = d
        return advanced_storage_schedule_weekly_model

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
