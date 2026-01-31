from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

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


T = TypeVar("T", bound="FileBackupJobModel")


@_attrs_define
class FileBackupJobModel:
    """File share backup job.

    Attributes:
        id (UUID): Job ID.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        is_disabled (bool): If `true`, the job is disabled.
        description (str | Unset): Job description.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job higher than other
            similar jobs and allocates resources to it in the first place.
        objects (list[FileBackupJobObjectModel] | Unset): Array of objects processed by the backup job.
        backup_repository (FileBackupJobPrimaryRepositoryModel | Unset): Primary backup repository for file share backup
            job.
        archive_repository (UnstructuredDataBackupJobArchiveRepositoryModel | Unset): Archive repository settings for
            unstructured data backup job.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    description: str | Unset = UNSET
    is_high_priority: bool | Unset = UNSET
    objects: list[FileBackupJobObjectModel] | Unset = UNSET
    backup_repository: FileBackupJobPrimaryRepositoryModel | Unset = UNSET
    archive_repository: UnstructuredDataBackupJobArchiveRepositoryModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        description = self.description

        is_high_priority = self.is_high_priority

        objects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.objects, Unset):
            objects = []
            for objects_item_data in self.objects:
                objects_item = objects_item_data.to_dict()
                objects.append(objects_item)

        backup_repository: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_repository, Unset):
            backup_repository = self.backup_repository.to_dict()

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
                "id": id,
                "name": name,
                "type": type_,
                "isDisabled": is_disabled,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if objects is not UNSET:
            field_dict["objects"] = objects
        if backup_repository is not UNSET:
            field_dict["backupRepository"] = backup_repository
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
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        description = d.pop("description", UNSET)

        is_high_priority = d.pop("isHighPriority", UNSET)

        _objects = d.pop("objects", UNSET)
        objects: list[FileBackupJobObjectModel] | Unset = UNSET
        if _objects is not UNSET:
            objects = []
            for objects_item_data in _objects:
                objects_item = FileBackupJobObjectModel.from_dict(objects_item_data)

                objects.append(objects_item)

        _backup_repository = d.pop("backupRepository", UNSET)
        backup_repository: FileBackupJobPrimaryRepositoryModel | Unset
        if isinstance(_backup_repository, Unset):
            backup_repository = UNSET
        else:
            backup_repository = FileBackupJobPrimaryRepositoryModel.from_dict(_backup_repository)

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

        file_backup_job_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
            description=description,
            is_high_priority=is_high_priority,
            objects=objects,
            backup_repository=backup_repository,
            archive_repository=archive_repository,
            schedule=schedule,
        )

        file_backup_job_model.additional_properties = d
        return file_backup_job_model

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
