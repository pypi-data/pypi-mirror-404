from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrAutoUnmountModel")


@_attrs_define
class FlrAutoUnmountModel:
    """Settings for automatic unmount of the file system.

    Attributes:
        is_enabled (bool): If `true`, the file system will be unmounted and the `FileLevelRestore` session will be
            stopped automatically after the specified time period of inactivity.
        no_activity_period_in_minutes (int | Unset): Time period in minutes. Default: 30.
    """

    is_enabled: bool
    no_activity_period_in_minutes: int | Unset = 30
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        no_activity_period_in_minutes = self.no_activity_period_in_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if no_activity_period_in_minutes is not UNSET:
            field_dict["noActivityPeriodInMinutes"] = no_activity_period_in_minutes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        no_activity_period_in_minutes = d.pop("noActivityPeriodInMinutes", UNSET)

        flr_auto_unmount_model = cls(
            is_enabled=is_enabled,
            no_activity_period_in_minutes=no_activity_period_in_minutes,
        )

        flr_auto_unmount_model.additional_properties = d
        return flr_auto_unmount_model

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
