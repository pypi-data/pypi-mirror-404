from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_copy_job_mode import EBackupCopyJobMode

T = TypeVar("T", bound="BackupCopyJobScheduleModel")


@_attrs_define
class BackupCopyJobScheduleModel:
    """Schedule for backup copy job.

    Attributes:
        type_ (EBackupCopyJobMode): Copy mode of backup copy job.
    """

    type_: EBackupCopyJobMode
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EBackupCopyJobMode(d.pop("type"))

        backup_copy_job_schedule_model = cls(
            type_=type_,
        )

        backup_copy_job_schedule_model.additional_properties = d
        return backup_copy_job_schedule_model

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
