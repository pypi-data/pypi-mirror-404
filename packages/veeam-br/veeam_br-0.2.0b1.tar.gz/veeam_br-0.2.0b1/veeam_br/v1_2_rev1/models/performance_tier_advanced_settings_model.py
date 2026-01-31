from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PerformanceTierAdvancedSettingsModel")


@_attrs_define
class PerformanceTierAdvancedSettingsModel:
    """Advanced settings of the performance tier.

    Attributes:
        per_vm_backup (bool | Unset): If `true`, Veeam Backup & Replication creates a separate backup file for every VM
            in the job.
        full_when_extent_offline (bool | Unset): If `true`, Veeam Backup & Replication creates a full backup file
            instead of an incremental backup file in case the required extent is offline.
    """

    per_vm_backup: bool | Unset = UNSET
    full_when_extent_offline: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        per_vm_backup = self.per_vm_backup

        full_when_extent_offline = self.full_when_extent_offline

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if per_vm_backup is not UNSET:
            field_dict["perVmBackup"] = per_vm_backup
        if full_when_extent_offline is not UNSET:
            field_dict["fullWhenExtentOffline"] = full_when_extent_offline

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        per_vm_backup = d.pop("perVmBackup", UNSET)

        full_when_extent_offline = d.pop("fullWhenExtentOffline", UNSET)

        performance_tier_advanced_settings_model = cls(
            per_vm_backup=per_vm_backup,
            full_when_extent_offline=full_when_extent_offline,
        )

        performance_tier_advanced_settings_model.additional_properties = d
        return performance_tier_advanced_settings_model

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
