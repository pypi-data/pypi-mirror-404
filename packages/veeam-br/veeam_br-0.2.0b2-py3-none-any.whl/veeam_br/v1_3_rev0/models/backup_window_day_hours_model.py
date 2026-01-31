from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_day_of_week import EDayOfWeek

T = TypeVar("T", bound="BackupWindowDayHoursModel")


@_attrs_define
class BackupWindowDayHoursModel:
    """Hourly scheme for a day.

    Attributes:
        day (EDayOfWeek): Day of the week.
        hours (str): String of 24 hours in the following
            format:<p>*1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1*<p>where *1* means permitted, *0* means denied.
    """

    day: EDayOfWeek
    hours: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        day = self.day.value

        hours = self.hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "day": day,
                "hours": hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        day = EDayOfWeek(d.pop("day"))

        hours = d.pop("hours")

        backup_window_day_hours_model = cls(
            day=day,
            hours=hours,
        )

        backup_window_day_hours_model.additional_properties = d
        return backup_window_day_hours_model

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
