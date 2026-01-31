from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_copy_job_mode import EBackupCopyJobMode
from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_copy_job_data_transfer_model import BackupCopyJobDataTransferModel
    from ..models.backup_copy_job_objects_model import BackupCopyJobObjectsModel
    from ..models.backup_copy_job_schedule_model import BackupCopyJobScheduleModel
    from ..models.backup_copy_job_target_model import BackupCopyJobTargetModel


T = TypeVar("T", bound="BackupCopyJobSpec")


@_attrs_define
class BackupCopyJobSpec:
    """Settings for backup copy job.

    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        mode (EBackupCopyJobMode): Copy mode of backup copy job.
        source_objects (BackupCopyJobObjectsModel): Included and excluded objects.
        target (BackupCopyJobTargetModel): Target repository for backup copy job.
        data_transfer (BackupCopyJobDataTransferModel | Unset): Data transfer settings.
        schedule (BackupCopyJobScheduleModel | Unset): Schedule for backup copy job.
    """

    name: str
    type_: EJobType
    description: str
    mode: EBackupCopyJobMode
    source_objects: BackupCopyJobObjectsModel
    target: BackupCopyJobTargetModel
    data_transfer: BackupCopyJobDataTransferModel | Unset = UNSET
    schedule: BackupCopyJobScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        description = self.description

        mode = self.mode.value

        source_objects = self.source_objects.to_dict()

        target = self.target.to_dict()

        data_transfer: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data_transfer, Unset):
            data_transfer = self.data_transfer.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "description": description,
                "mode": mode,
                "sourceObjects": source_objects,
                "target": target,
            }
        )
        if data_transfer is not UNSET:
            field_dict["dataTransfer"] = data_transfer
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_copy_job_data_transfer_model import BackupCopyJobDataTransferModel
        from ..models.backup_copy_job_objects_model import BackupCopyJobObjectsModel
        from ..models.backup_copy_job_schedule_model import BackupCopyJobScheduleModel
        from ..models.backup_copy_job_target_model import BackupCopyJobTargetModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        mode = EBackupCopyJobMode(d.pop("mode"))

        source_objects = BackupCopyJobObjectsModel.from_dict(d.pop("sourceObjects"))

        target = BackupCopyJobTargetModel.from_dict(d.pop("target"))

        _data_transfer = d.pop("dataTransfer", UNSET)
        data_transfer: BackupCopyJobDataTransferModel | Unset
        if isinstance(_data_transfer, Unset):
            data_transfer = UNSET
        else:
            data_transfer = BackupCopyJobDataTransferModel.from_dict(_data_transfer)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupCopyJobScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupCopyJobScheduleModel.from_dict(_schedule)

        backup_copy_job_spec = cls(
            name=name,
            type_=type_,
            description=description,
            mode=mode,
            source_objects=source_objects,
            target=target,
            data_transfer=data_transfer,
            schedule=schedule,
        )

        backup_copy_job_spec.additional_properties = d
        return backup_copy_job_spec

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
