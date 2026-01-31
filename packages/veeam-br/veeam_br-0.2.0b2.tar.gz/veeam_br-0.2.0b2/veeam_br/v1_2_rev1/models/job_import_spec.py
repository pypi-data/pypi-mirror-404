from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType

if TYPE_CHECKING:
    from ..models.backup_job_guest_processing_import_model import BackupJobGuestProcessingImportModel
    from ..models.backup_job_storage_import_model import BackupJobStorageImportModel
    from ..models.backup_job_virtual_machines_spec import BackupJobVirtualMachinesSpec
    from ..models.backup_schedule_model import BackupScheduleModel


T = TypeVar("T", bound="JobImportSpec")


@_attrs_define
class JobImportSpec:
    """
    Attributes:
        name (str): Name of the job.
        description (str): Description of the job.
        is_high_priority (bool): If `true`, the resource scheduler prioritizes this job higher than other similar jobs
            and allocates resources to it in the first place.
        type_ (EJobType): Type of the job.
        virtual_machines (BackupJobVirtualMachinesSpec): Included and excluded objects.
        storage (BackupJobStorageImportModel): Backup storage settings.
        guest_processing (BackupJobGuestProcessingImportModel): Guest processing settings.
        schedule (BackupScheduleModel): Job scheduling options.
    """

    name: str
    description: str
    is_high_priority: bool
    type_: EJobType
    virtual_machines: BackupJobVirtualMachinesSpec
    storage: BackupJobStorageImportModel
    guest_processing: BackupJobGuestProcessingImportModel
    schedule: BackupScheduleModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        is_high_priority = self.is_high_priority

        type_ = self.type_.value

        virtual_machines = self.virtual_machines.to_dict()

        storage = self.storage.to_dict()

        guest_processing = self.guest_processing.to_dict()

        schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "isHighPriority": is_high_priority,
                "type": type_,
                "virtualMachines": virtual_machines,
                "storage": storage,
                "guestProcessing": guest_processing,
                "schedule": schedule,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_guest_processing_import_model import BackupJobGuestProcessingImportModel
        from ..models.backup_job_storage_import_model import BackupJobStorageImportModel
        from ..models.backup_job_virtual_machines_spec import BackupJobVirtualMachinesSpec
        from ..models.backup_schedule_model import BackupScheduleModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        is_high_priority = d.pop("isHighPriority")

        type_ = EJobType(d.pop("type"))

        virtual_machines = BackupJobVirtualMachinesSpec.from_dict(d.pop("virtualMachines"))

        storage = BackupJobStorageImportModel.from_dict(d.pop("storage"))

        guest_processing = BackupJobGuestProcessingImportModel.from_dict(d.pop("guestProcessing"))

        schedule = BackupScheduleModel.from_dict(d.pop("schedule"))

        job_import_spec = cls(
            name=name,
            description=description,
            is_high_priority=is_high_priority,
            type_=type_,
            virtual_machines=virtual_machines,
            storage=storage,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        job_import_spec.additional_properties = d
        return job_import_spec

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
