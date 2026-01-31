from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.gfs_policy_settings_monthly_model import GFSPolicySettingsMonthlyModel
    from ..models.gfs_policy_settings_weekly_model import GFSPolicySettingsWeeklyModel
    from ..models.gfs_policy_settings_yearly_model import GFSPolicySettingsYearlyModel


T = TypeVar("T", bound="BackupCopyGFSPolicySettingsModel")


@_attrs_define
class BackupCopyGFSPolicySettingsModel:
    """GFS retention policy settings.

    Attributes:
        is_enabled (bool): If `true`, the long-term (GFS) retention policy is enabled.
        weekly (GFSPolicySettingsWeeklyModel | Unset): Weekly GFS retention policy.
        monthly (GFSPolicySettingsMonthlyModel | Unset): Monthly GFS retention policy.
        yearly (GFSPolicySettingsYearlyModel | Unset): Yearly GFS retention policy.
        read_entire_restore_point (bool | Unset): If `true`, the entire restore point from source will be read instead
            of synthesizing it from increment.
    """

    is_enabled: bool
    weekly: GFSPolicySettingsWeeklyModel | Unset = UNSET
    monthly: GFSPolicySettingsMonthlyModel | Unset = UNSET
    yearly: GFSPolicySettingsYearlyModel | Unset = UNSET
    read_entire_restore_point: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        weekly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.weekly, Unset):
            weekly = self.weekly.to_dict()

        monthly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.monthly, Unset):
            monthly = self.monthly.to_dict()

        yearly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.yearly, Unset):
            yearly = self.yearly.to_dict()

        read_entire_restore_point = self.read_entire_restore_point

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
        if yearly is not UNSET:
            field_dict["yearly"] = yearly
        if read_entire_restore_point is not UNSET:
            field_dict["readEntireRestorePoint"] = read_entire_restore_point

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.gfs_policy_settings_monthly_model import GFSPolicySettingsMonthlyModel
        from ..models.gfs_policy_settings_weekly_model import GFSPolicySettingsWeeklyModel
        from ..models.gfs_policy_settings_yearly_model import GFSPolicySettingsYearlyModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _weekly = d.pop("weekly", UNSET)
        weekly: GFSPolicySettingsWeeklyModel | Unset
        if isinstance(_weekly, Unset):
            weekly = UNSET
        else:
            weekly = GFSPolicySettingsWeeklyModel.from_dict(_weekly)

        _monthly = d.pop("monthly", UNSET)
        monthly: GFSPolicySettingsMonthlyModel | Unset
        if isinstance(_monthly, Unset):
            monthly = UNSET
        else:
            monthly = GFSPolicySettingsMonthlyModel.from_dict(_monthly)

        _yearly = d.pop("yearly", UNSET)
        yearly: GFSPolicySettingsYearlyModel | Unset
        if isinstance(_yearly, Unset):
            yearly = UNSET
        else:
            yearly = GFSPolicySettingsYearlyModel.from_dict(_yearly)

        read_entire_restore_point = d.pop("readEntireRestorePoint", UNSET)

        backup_copy_gfs_policy_settings_model = cls(
            is_enabled=is_enabled,
            weekly=weekly,
            monthly=monthly,
            yearly=yearly,
            read_entire_restore_point=read_entire_restore_point,
        )

        backup_copy_gfs_policy_settings_model.additional_properties = d
        return backup_copy_gfs_policy_settings_model

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
