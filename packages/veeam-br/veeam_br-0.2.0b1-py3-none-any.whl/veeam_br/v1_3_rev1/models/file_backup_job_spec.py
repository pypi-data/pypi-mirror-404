from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.file_backup_job_object_model import FileBackupJobObjectModel
    from ..models.file_backup_job_primary_repository_model import FileBackupJobPrimaryRepositoryModel
    from ..models.unstructured_data_backup_job_archive_repository_model import (
        UnstructuredDataBackupJobArchiveRepositoryModel,
    )


T = TypeVar("T", bound="FileBackupJobSpec")


@_attrs_define
class FileBackupJobSpec:
    """Settings for file share backup jobs.

    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        objects (list[FileBackupJobObjectModel]): Array of objects processed by the backup job.
        backup_repository (FileBackupJobPrimaryRepositoryModel): Primary backup repository for file share backup job.
        description (str | Unset): Job description.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job higher than other
            similar jobs and allocates resources to it in the first place.
        archive_repository (UnstructuredDataBackupJobArchiveRepositoryModel | Unset): Archive repository settings for
            unstructured data backup job.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    name: str
    type_: EJobType
    objects: list[FileBackupJobObjectModel]
    backup_repository: FileBackupJobPrimaryRepositoryModel
    description: str | Unset = UNSET
    is_high_priority: bool | Unset = UNSET
    archive_repository: UnstructuredDataBackupJobArchiveRepositoryModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        objects = []
        for objects_item_data in self.objects:
            objects_item = objects_item_data.to_dict()
            objects.append(objects_item)

        backup_repository = self.backup_repository.to_dict()

        description = self.description

        is_high_priority = self.is_high_priority

        archive_repository: dict[str, Any] | Unset = UNSET
        if not isinstance(self.archive_repository, Unset):
            archive_repository = self.archive_repository.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "objects": objects,
                "backupRepository": backup_repository,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if archive_repository is not UNSET:
            field_dict["archiveRepository"] = archive_repository
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.file_backup_job_object_model import FileBackupJobObjectModel
        from ..models.file_backup_job_primary_repository_model import FileBackupJobPrimaryRepositoryModel
        from ..models.unstructured_data_backup_job_archive_repository_model import (
            UnstructuredDataBackupJobArchiveRepositoryModel,
        )

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        objects = []
        _objects = d.pop("objects")
        for objects_item_data in _objects:
            objects_item = FileBackupJobObjectModel.from_dict(objects_item_data)

            objects.append(objects_item)

        backup_repository = FileBackupJobPrimaryRepositoryModel.from_dict(d.pop("backupRepository"))

        description = d.pop("description", UNSET)

        is_high_priority = d.pop("isHighPriority", UNSET)

        _archive_repository = d.pop("archiveRepository", UNSET)
        archive_repository: UnstructuredDataBackupJobArchiveRepositoryModel | Unset
        if isinstance(_archive_repository, Unset):
            archive_repository = UNSET
        else:
            archive_repository = UnstructuredDataBackupJobArchiveRepositoryModel.from_dict(_archive_repository)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        file_backup_job_spec = cls(
            name=name,
            type_=type_,
            objects=objects,
            backup_repository=backup_repository,
            description=description,
            is_high_priority=is_high_priority,
            archive_repository=archive_repository,
            schedule=schedule,
        )

        file_backup_job_spec.additional_properties = d
        return file_backup_job_spec

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
