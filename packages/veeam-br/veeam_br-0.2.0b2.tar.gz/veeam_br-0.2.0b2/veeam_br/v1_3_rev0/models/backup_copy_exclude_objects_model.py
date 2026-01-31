from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.job_object_model import JobObjectModel


T = TypeVar("T", bound="BackupCopyExcludeObjectsModel")


@_attrs_define
class BackupCopyExcludeObjectsModel:
    """Excluded objects.

    Attributes:
        jobs (list[JobObjectModel] | Unset): Array of jobs, excluded from the job.
        objects (list[InventoryObjectModel] | Unset): Array of objects, excluded from the job.
    """

    jobs: list[JobObjectModel] | Unset = UNSET
    objects: list[InventoryObjectModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)

        objects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.objects, Unset):
            objects = []
            for objects_item_data in self.objects:
                objects_item = objects_item_data.to_dict()
                objects.append(objects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobs is not UNSET:
            field_dict["jobs"] = jobs
        if objects is not UNSET:
            field_dict["objects"] = objects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.job_object_model import JobObjectModel

        d = dict(src_dict)
        _jobs = d.pop("jobs", UNSET)
        jobs: list[JobObjectModel] | Unset = UNSET
        if _jobs is not UNSET:
            jobs = []
            for jobs_item_data in _jobs:
                jobs_item = JobObjectModel.from_dict(jobs_item_data)

                jobs.append(jobs_item)

        _objects = d.pop("objects", UNSET)
        objects: list[InventoryObjectModel] | Unset = UNSET
        if _objects is not UNSET:
            objects = []
            for objects_item_data in _objects:
                objects_item = InventoryObjectModel.from_dict(objects_item_data)

                objects.append(objects_item)

        backup_copy_exclude_objects_model = cls(
            jobs=jobs,
            objects=objects,
        )

        backup_copy_exclude_objects_model.additional_properties = d
        return backup_copy_exclude_objects_model

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
