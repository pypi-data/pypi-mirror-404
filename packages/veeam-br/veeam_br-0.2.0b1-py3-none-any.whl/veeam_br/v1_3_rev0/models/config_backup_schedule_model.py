from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_daily_model import ScheduleDailyModel
    from ..models.schedule_monthly_model import ScheduleMonthlyModel


T = TypeVar("T", bound="ConfigBackupScheduleModel")


@_attrs_define
class ConfigBackupScheduleModel:
    """Scheduling settings.

    Attributes:
        is_enabled (bool): If `true`, backup scheduling is enabled.
        daily (ScheduleDailyModel | Unset): Daily scheduling options.
        monthly (ScheduleMonthlyModel | Unset): Monthly scheduling options.
    """

    is_enabled: bool
    daily: ScheduleDailyModel | Unset = UNSET
    monthly: ScheduleMonthlyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        daily: dict[str, Any] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        monthly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.monthly, Unset):
            monthly = self.monthly.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if daily is not UNSET:
            field_dict["daily"] = daily
        if monthly is not UNSET:
            field_dict["monthly"] = monthly

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_daily_model import ScheduleDailyModel
        from ..models.schedule_monthly_model import ScheduleMonthlyModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _daily = d.pop("daily", UNSET)
        daily: ScheduleDailyModel | Unset
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        _monthly = d.pop("monthly", UNSET)
        monthly: ScheduleMonthlyModel | Unset
        if isinstance(_monthly, Unset):
            monthly = UNSET
        else:
            monthly = ScheduleMonthlyModel.from_dict(_monthly)

        config_backup_schedule_model = cls(
            is_enabled=is_enabled,
            daily=daily,
            monthly=monthly,
        )

        config_backup_schedule_model.additional_properties = d
        return config_backup_schedule_model

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
