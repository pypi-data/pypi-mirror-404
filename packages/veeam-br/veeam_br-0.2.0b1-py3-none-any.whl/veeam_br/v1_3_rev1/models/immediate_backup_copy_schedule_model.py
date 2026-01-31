from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_copy_job_mode import EBackupCopyJobMode
from ..models.e_immediate_schedule_model import EImmediateScheduleModel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_window_setting_model import BackupWindowSettingModel


T = TypeVar("T", bound="ImmediateBackupCopyScheduleModel")


@_attrs_define
class ImmediateBackupCopyScheduleModel:
    """Scheduling options for backup copy jobs with the immediate copy mode.

    Attributes:
        type_ (EBackupCopyJobMode): Copy mode of backup copy job.
        schedule_mode (EImmediateScheduleModel): Data transfer mode.
        backup_window (BackupWindowSettingModel | Unset): Time scheme that defines permitted days and hours for the job
            to start.
    """

    type_: EBackupCopyJobMode
    schedule_mode: EImmediateScheduleModel
    backup_window: BackupWindowSettingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        schedule_mode = self.schedule_mode.value

        backup_window: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_window, Unset):
            backup_window = self.backup_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "scheduleMode": schedule_mode,
            }
        )
        if backup_window is not UNSET:
            field_dict["backupWindow"] = backup_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_window_setting_model import BackupWindowSettingModel

        d = dict(src_dict)
        type_ = EBackupCopyJobMode(d.pop("type"))

        schedule_mode = EImmediateScheduleModel(d.pop("scheduleMode"))

        _backup_window = d.pop("backupWindow", UNSET)
        backup_window: BackupWindowSettingModel | Unset
        if isinstance(_backup_window, Unset):
            backup_window = UNSET
        else:
            backup_window = BackupWindowSettingModel.from_dict(_backup_window)

        immediate_backup_copy_schedule_model = cls(
            type_=type_,
            schedule_mode=schedule_mode,
            backup_window=backup_window,
        )

        immediate_backup_copy_schedule_model.additional_properties = d
        return immediate_backup_copy_schedule_model

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
