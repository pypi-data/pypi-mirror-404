from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_guest_processing_model import BackupJobGuestProcessingModel
    from ..models.backup_job_storage_model import BackupJobStorageModel
    from ..models.backup_job_virtual_machines_model import BackupJobVirtualMachinesModel
    from ..models.backup_schedule_model import BackupScheduleModel


T = TypeVar("T", bound="CloudDirectorBackupJobModel")


@_attrs_define
class CloudDirectorBackupJobModel:
    """VMware Cloud Director backup job.

    Attributes:
        id (UUID): Job ID.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        is_disabled (bool): If `true`, the job is disabled.
        description (str): Description of the job.
        virtual_machines (BackupJobVirtualMachinesModel): Included and excluded objects.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job over other similar jobs
            and allocates resources to it first.
        storage (BackupJobStorageModel | Unset): VMware vSphere backup storage settings.
        guest_processing (BackupJobGuestProcessingModel | Unset): Guest processing settings.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    description: str
    virtual_machines: BackupJobVirtualMachinesModel
    is_high_priority: bool | Unset = UNSET
    storage: BackupJobStorageModel | Unset = UNSET
    guest_processing: BackupJobGuestProcessingModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        description = self.description

        virtual_machines = self.virtual_machines.to_dict()

        is_high_priority = self.is_high_priority

        storage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage, Unset):
            storage = self.storage.to_dict()

        guest_processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_processing, Unset):
            guest_processing = self.guest_processing.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "isDisabled": is_disabled,
                "description": description,
                "virtualMachines": virtual_machines,
            }
        )
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if storage is not UNSET:
            field_dict["storage"] = storage
        if guest_processing is not UNSET:
            field_dict["guestProcessing"] = guest_processing
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_guest_processing_model import BackupJobGuestProcessingModel
        from ..models.backup_job_storage_model import BackupJobStorageModel
        from ..models.backup_job_virtual_machines_model import BackupJobVirtualMachinesModel
        from ..models.backup_schedule_model import BackupScheduleModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        description = d.pop("description")

        virtual_machines = BackupJobVirtualMachinesModel.from_dict(d.pop("virtualMachines"))

        is_high_priority = d.pop("isHighPriority", UNSET)

        _storage = d.pop("storage", UNSET)
        storage: BackupJobStorageModel | Unset
        if isinstance(_storage, Unset):
            storage = UNSET
        else:
            storage = BackupJobStorageModel.from_dict(_storage)

        _guest_processing = d.pop("guestProcessing", UNSET)
        guest_processing: BackupJobGuestProcessingModel | Unset
        if isinstance(_guest_processing, Unset):
            guest_processing = UNSET
        else:
            guest_processing = BackupJobGuestProcessingModel.from_dict(_guest_processing)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        cloud_director_backup_job_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
            description=description,
            virtual_machines=virtual_machines,
            is_high_priority=is_high_priority,
            storage=storage,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        cloud_director_backup_job_model.additional_properties = d
        return cloud_director_backup_job_model

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
