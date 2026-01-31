from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_file_backup_copy_job_schedule_type import EFileBackupCopyJobScheduleType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_backup_window_model import ScheduleBackupWindowModel


T = TypeVar("T", bound="FileBackupCopyJobScheduleModel")


@_attrs_define
class FileBackupCopyJobScheduleModel:
    """
    Attributes:
        type_ (EFileBackupCopyJobScheduleType | Unset):
        custom_window (ScheduleBackupWindowModel | Unset): Backup window settings.
    """

    type_: EFileBackupCopyJobScheduleType | Unset = UNSET
    custom_window: ScheduleBackupWindowModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        custom_window: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_window, Unset):
            custom_window = self.custom_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if custom_window is not UNSET:
            field_dict["customWindow"] = custom_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_backup_window_model import ScheduleBackupWindowModel

        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: EFileBackupCopyJobScheduleType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EFileBackupCopyJobScheduleType(_type_)

        _custom_window = d.pop("customWindow", UNSET)
        custom_window: ScheduleBackupWindowModel | Unset
        if isinstance(_custom_window, Unset):
            custom_window = UNSET
        else:
            custom_window = ScheduleBackupWindowModel.from_dict(_custom_window)

        file_backup_copy_job_schedule_model = cls(
            type_=type_,
            custom_window=custom_window,
        )

        file_backup_copy_job_schedule_model.additional_properties = d
        return file_backup_copy_job_schedule_model

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
