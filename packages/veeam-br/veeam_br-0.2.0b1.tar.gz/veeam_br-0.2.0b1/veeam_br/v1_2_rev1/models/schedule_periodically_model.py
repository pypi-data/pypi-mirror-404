from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_periodically_kinds import EPeriodicallyKinds
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_window_setting_model import BackupWindowSettingModel


T = TypeVar("T", bound="SchedulePeriodicallyModel")


@_attrs_define
class SchedulePeriodicallyModel:
    """Periodic scheduling options.

    Attributes:
        is_enabled (bool): If `true`, periodic schedule is enabled. Default: False.
        periodically_kind (EPeriodicallyKinds | Unset): Time unit for periodic job scheduling.
        frequency (int | Unset): Number of time units that defines the time interval.
        backup_window (BackupWindowSettingModel | Unset): Time scheme that defines permitted days and hours for the job
            to start.
        start_time_within_an_hour (int | Unset): Start time within an hour, in minutes.
    """

    is_enabled: bool = False
    periodically_kind: EPeriodicallyKinds | Unset = UNSET
    frequency: int | Unset = UNSET
    backup_window: BackupWindowSettingModel | Unset = UNSET
    start_time_within_an_hour: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        periodically_kind: str | Unset = UNSET
        if not isinstance(self.periodically_kind, Unset):
            periodically_kind = self.periodically_kind.value

        frequency = self.frequency

        backup_window: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_window, Unset):
            backup_window = self.backup_window.to_dict()

        start_time_within_an_hour = self.start_time_within_an_hour

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if periodically_kind is not UNSET:
            field_dict["periodicallyKind"] = periodically_kind
        if frequency is not UNSET:
            field_dict["frequency"] = frequency
        if backup_window is not UNSET:
            field_dict["backupWindow"] = backup_window
        if start_time_within_an_hour is not UNSET:
            field_dict["startTimeWithinAnHour"] = start_time_within_an_hour

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_window_setting_model import BackupWindowSettingModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _periodically_kind = d.pop("periodicallyKind", UNSET)
        periodically_kind: EPeriodicallyKinds | Unset
        if isinstance(_periodically_kind, Unset):
            periodically_kind = UNSET
        else:
            periodically_kind = EPeriodicallyKinds(_periodically_kind)

        frequency = d.pop("frequency", UNSET)

        _backup_window = d.pop("backupWindow", UNSET)
        backup_window: BackupWindowSettingModel | Unset
        if isinstance(_backup_window, Unset):
            backup_window = UNSET
        else:
            backup_window = BackupWindowSettingModel.from_dict(_backup_window)

        start_time_within_an_hour = d.pop("startTimeWithinAnHour", UNSET)

        schedule_periodically_model = cls(
            is_enabled=is_enabled,
            periodically_kind=periodically_kind,
            frequency=frequency,
            backup_window=backup_window,
            start_time_within_an_hour=start_time_within_an_hour,
        )

        schedule_periodically_model.additional_properties = d
        return schedule_periodically_model

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
