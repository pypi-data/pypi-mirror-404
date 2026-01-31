from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_rpo_monitor_model import BackupRPOMonitorModel
    from ..models.log_backup_rpo_monitor_model import LogBackupRPOMonitorModel


T = TypeVar("T", bound="BackupCopyJobRPOMonitorModel")


@_attrs_define
class BackupCopyJobRPOMonitorModel:
    """RPO monitor settings for backup copy job.

    Attributes:
        new_backup_threshold (BackupRPOMonitorModel | Unset): RPO monitor settings if new backup is not copied.
        new_log_backup_threshold (LogBackupRPOMonitorModel | Unset): RPO monitor settings if new log backup is not
            copied.
    """

    new_backup_threshold: BackupRPOMonitorModel | Unset = UNSET
    new_log_backup_threshold: LogBackupRPOMonitorModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_backup_threshold: dict[str, Any] | Unset = UNSET
        if not isinstance(self.new_backup_threshold, Unset):
            new_backup_threshold = self.new_backup_threshold.to_dict()

        new_log_backup_threshold: dict[str, Any] | Unset = UNSET
        if not isinstance(self.new_log_backup_threshold, Unset):
            new_log_backup_threshold = self.new_log_backup_threshold.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if new_backup_threshold is not UNSET:
            field_dict["newBackupThreshold"] = new_backup_threshold
        if new_log_backup_threshold is not UNSET:
            field_dict["newLogBackupThreshold"] = new_log_backup_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_rpo_monitor_model import BackupRPOMonitorModel
        from ..models.log_backup_rpo_monitor_model import LogBackupRPOMonitorModel

        d = dict(src_dict)
        _new_backup_threshold = d.pop("newBackupThreshold", UNSET)
        new_backup_threshold: BackupRPOMonitorModel | Unset
        if isinstance(_new_backup_threshold, Unset):
            new_backup_threshold = UNSET
        else:
            new_backup_threshold = BackupRPOMonitorModel.from_dict(_new_backup_threshold)

        _new_log_backup_threshold = d.pop("newLogBackupThreshold", UNSET)
        new_log_backup_threshold: LogBackupRPOMonitorModel | Unset
        if isinstance(_new_log_backup_threshold, Unset):
            new_log_backup_threshold = UNSET
        else:
            new_log_backup_threshold = LogBackupRPOMonitorModel.from_dict(_new_log_backup_threshold)

        backup_copy_job_rpo_monitor_model = cls(
            new_backup_threshold=new_backup_threshold,
            new_log_backup_threshold=new_log_backup_threshold,
        )

        backup_copy_job_rpo_monitor_model.additional_properties = d
        return backup_copy_job_rpo_monitor_model

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
