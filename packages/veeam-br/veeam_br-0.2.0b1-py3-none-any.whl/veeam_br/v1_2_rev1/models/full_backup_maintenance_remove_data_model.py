from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FullBackupMaintenanceRemoveDataModel")


@_attrs_define
class FullBackupMaintenanceRemoveDataModel:
    """Backup data setting for deleted VMs.

    Attributes:
        is_enabled (bool): If `true`, Veeam Backup & Replication keeps the backup data of deleted VMs for the
            `afterDays` number of days.
        after_days (int | Unset): Number of days.
    """

    is_enabled: bool
    after_days: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        after_days = self.after_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if after_days is not UNSET:
            field_dict["afterDays"] = after_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        after_days = d.pop("afterDays", UNSET)

        full_backup_maintenance_remove_data_model = cls(
            is_enabled=is_enabled,
            after_days=after_days,
        )

        full_backup_maintenance_remove_data_model.additional_properties = d
        return full_backup_maintenance_remove_data_model

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
