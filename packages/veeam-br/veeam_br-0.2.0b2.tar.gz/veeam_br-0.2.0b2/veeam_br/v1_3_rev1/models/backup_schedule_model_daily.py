from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_daily_model import ScheduleDailyModel


T = TypeVar("T", bound="BackupScheduleModelDaily")


@_attrs_define
class BackupScheduleModelDaily:
    """Job scheduling options - Daily.

    Attributes:
        run_automatically (bool): If `true`, job scheduling is enabled. Default: False.
        daily (ScheduleDailyModel | Unset): Daily scheduling options.
    """

    run_automatically: bool = False
    daily: ScheduleDailyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_automatically = self.run_automatically

        daily: dict[str, Any] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runAutomatically": run_automatically,
            }
        )
        if daily is not UNSET:
            field_dict["daily"] = daily

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_daily_model import ScheduleDailyModel

        d = dict(src_dict)
        run_automatically = d.pop("runAutomatically")

        _daily = d.pop("daily", UNSET)
        daily: ScheduleDailyModel | Unset
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        backup_schedule_model_daily = cls(
            run_automatically=run_automatically,
            daily=daily,
        )

        backup_schedule_model_daily.additional_properties = d
        return backup_schedule_model_daily

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
