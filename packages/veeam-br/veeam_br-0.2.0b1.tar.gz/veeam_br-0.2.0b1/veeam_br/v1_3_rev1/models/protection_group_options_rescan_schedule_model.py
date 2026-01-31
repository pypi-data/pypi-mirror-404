from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
    from ..models.schedule_daily_model import ScheduleDailyModel
    from ..models.schedule_periodically_model import SchedulePeriodicallyModel


T = TypeVar("T", bound="ProtectionGroupOptionsRescanScheduleModel")


@_attrs_define
class ProtectionGroupOptionsRescanScheduleModel:
    """Rescan schedule settings for the protection group.

    Attributes:
        daily (ScheduleDailyModel | Unset): Daily scheduling options.
        periodically (SchedulePeriodicallyModel | Unset): Periodic scheduling options.
        continuously (ScheduleBackupWindowModel | Unset): Backup window settings.
    """

    daily: ScheduleDailyModel | Unset = UNSET
    periodically: SchedulePeriodicallyModel | Unset = UNSET
    continuously: ScheduleBackupWindowModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        daily: dict[str, Any] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        periodically: dict[str, Any] | Unset = UNSET
        if not isinstance(self.periodically, Unset):
            periodically = self.periodically.to_dict()

        continuously: dict[str, Any] | Unset = UNSET
        if not isinstance(self.continuously, Unset):
            continuously = self.continuously.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if daily is not UNSET:
            field_dict["daily"] = daily
        if periodically is not UNSET:
            field_dict["periodically"] = periodically
        if continuously is not UNSET:
            field_dict["continuously"] = continuously

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
        from ..models.schedule_daily_model import ScheduleDailyModel
        from ..models.schedule_periodically_model import SchedulePeriodicallyModel

        d = dict(src_dict)
        _daily = d.pop("daily", UNSET)
        daily: ScheduleDailyModel | Unset
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        _periodically = d.pop("periodically", UNSET)
        periodically: SchedulePeriodicallyModel | Unset
        if isinstance(_periodically, Unset):
            periodically = UNSET
        else:
            periodically = SchedulePeriodicallyModel.from_dict(_periodically)

        _continuously = d.pop("continuously", UNSET)
        continuously: ScheduleBackupWindowModel | Unset
        if isinstance(_continuously, Unset):
            continuously = UNSET
        else:
            continuously = ScheduleBackupWindowModel.from_dict(_continuously)

        protection_group_options_rescan_schedule_model = cls(
            daily=daily,
            periodically=periodically,
            continuously=continuously,
        )

        protection_group_options_rescan_schedule_model.additional_properties = d
        return protection_group_options_rescan_schedule_model

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
