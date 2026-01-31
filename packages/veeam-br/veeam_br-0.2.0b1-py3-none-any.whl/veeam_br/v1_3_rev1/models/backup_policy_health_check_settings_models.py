from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.advanced_storage_schedule_monthly_model import AdvancedStorageScheduleMonthlyModel
    from ..models.advanced_storage_schedule_weekly_model import AdvancedStorageScheduleWeeklyModel


T = TypeVar("T", bound="BackupPolicyHealthCheckSettingsModels")


@_attrs_define
class BackupPolicyHealthCheckSettingsModels:
    """Health check settings for unstructured data.

    Attributes:
        is_enabled (bool): If `true`, health check is enabled.
        weekly (AdvancedStorageScheduleWeeklyModel | Unset): Weekly schedule settings.
        monthly (AdvancedStorageScheduleMonthlyModel | Unset): Monthly schedule settings.
        is_full_health_check_enabled (bool | Unset): If `true`, full health check is enabled. Only valid for object
            storage repositories.
    """

    is_enabled: bool
    weekly: AdvancedStorageScheduleWeeklyModel | Unset = UNSET
    monthly: AdvancedStorageScheduleMonthlyModel | Unset = UNSET
    is_full_health_check_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        weekly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.weekly, Unset):
            weekly = self.weekly.to_dict()

        monthly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.monthly, Unset):
            monthly = self.monthly.to_dict()

        is_full_health_check_enabled = self.is_full_health_check_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if weekly is not UNSET:
            field_dict["weekly"] = weekly
        if monthly is not UNSET:
            field_dict["monthly"] = monthly
        if is_full_health_check_enabled is not UNSET:
            field_dict["isFullHealthCheckEnabled"] = is_full_health_check_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.advanced_storage_schedule_monthly_model import AdvancedStorageScheduleMonthlyModel
        from ..models.advanced_storage_schedule_weekly_model import AdvancedStorageScheduleWeeklyModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _weekly = d.pop("weekly", UNSET)
        weekly: AdvancedStorageScheduleWeeklyModel | Unset
        if isinstance(_weekly, Unset):
            weekly = UNSET
        else:
            weekly = AdvancedStorageScheduleWeeklyModel.from_dict(_weekly)

        _monthly = d.pop("monthly", UNSET)
        monthly: AdvancedStorageScheduleMonthlyModel | Unset
        if isinstance(_monthly, Unset):
            monthly = UNSET
        else:
            monthly = AdvancedStorageScheduleMonthlyModel.from_dict(_monthly)

        is_full_health_check_enabled = d.pop("isFullHealthCheckEnabled", UNSET)

        backup_policy_health_check_settings_models = cls(
            is_enabled=is_enabled,
            weekly=weekly,
            monthly=monthly,
            is_full_health_check_enabled=is_full_health_check_enabled,
        )

        backup_policy_health_check_settings_models.additional_properties = d
        return backup_policy_health_check_settings_models

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
