from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_window_setting_model import BackupWindowSettingModel


T = TypeVar("T", bound="ScheduleBackupWindowModel")


@_attrs_define
class ScheduleBackupWindowModel:
    """Backup window settings.

    Attributes:
        is_enabled (bool): If `true`, backup window is enabled. Default: False.
        backup_window (BackupWindowSettingModel | Unset): Time scheme that defines permitted days and hours for the job
            to start.
    """

    is_enabled: bool = False
    backup_window: BackupWindowSettingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        backup_window: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_window, Unset):
            backup_window = self.backup_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if backup_window is not UNSET:
            field_dict["backupWindow"] = backup_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_window_setting_model import BackupWindowSettingModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _backup_window = d.pop("backupWindow", UNSET)
        backup_window: BackupWindowSettingModel | Unset
        if isinstance(_backup_window, Unset):
            backup_window = UNSET
        else:
            backup_window = BackupWindowSettingModel.from_dict(_backup_window)

        schedule_backup_window_model = cls(
            is_enabled=is_enabled,
            backup_window=backup_window,
        )

        schedule_backup_window_model.additional_properties = d
        return schedule_backup_window_model

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
