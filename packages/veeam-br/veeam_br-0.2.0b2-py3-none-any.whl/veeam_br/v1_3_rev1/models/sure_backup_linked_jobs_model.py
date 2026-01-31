from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.job_object_model import JobObjectModel


T = TypeVar("T", bound="SureBackupLinkedJobsModel")


@_attrs_define
class SureBackupLinkedJobsModel:
    """Veeam Backup for Microsoft Azure, Veeam Backup for AWS, or Veeam Backup for Google Cloud backup policies with
    machines that you want to verify with the SureBackup job.

        Attributes:
            includes (list[JobObjectModel]): Array of backup policies. To get information about backup policies, run the
                [Get All Job States](Jobs#operation/GetAllJobsStates) request and filter the results by job type&#58;
                `CloudBackupAzure`, `CloudBackupAWS` or `CloudBackupGoogle`.
            excludes (list[InventoryObjectModel] | Unset): Array of objects that the SureBackup job excludes from
                processing. Specify only machines that are added to the linked backup policies.
            max_concurrent_machines_count (int | Unset): Maximum number of machines that can be processed at the same time.
            process_random_machines (bool | Unset): If `true`, only a number of random machines are tested.
            max_random_machines_count (int | Unset): Maximum number of machines that must be randomly tested.
    """

    includes: list[JobObjectModel]
    excludes: list[InventoryObjectModel] | Unset = UNSET
    max_concurrent_machines_count: int | Unset = UNSET
    process_random_machines: bool | Unset = UNSET
    max_random_machines_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        includes = []
        for includes_item_data in self.includes:
            includes_item = includes_item_data.to_dict()
            includes.append(includes_item)

        excludes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = []
            for excludes_item_data in self.excludes:
                excludes_item = excludes_item_data.to_dict()
                excludes.append(excludes_item)

        max_concurrent_machines_count = self.max_concurrent_machines_count

        process_random_machines = self.process_random_machines

        max_random_machines_count = self.max_random_machines_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes
        if max_concurrent_machines_count is not UNSET:
            field_dict["maxConcurrentMachinesCount"] = max_concurrent_machines_count
        if process_random_machines is not UNSET:
            field_dict["processRandomMachines"] = process_random_machines
        if max_random_machines_count is not UNSET:
            field_dict["maxRandomMachinesCount"] = max_random_machines_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.job_object_model import JobObjectModel

        d = dict(src_dict)
        includes = []
        _includes = d.pop("includes")
        for includes_item_data in _includes:
            includes_item = JobObjectModel.from_dict(includes_item_data)

            includes.append(includes_item)

        _excludes = d.pop("excludes", UNSET)
        excludes: list[InventoryObjectModel] | Unset = UNSET
        if _excludes is not UNSET:
            excludes = []
            for excludes_item_data in _excludes:
                excludes_item = InventoryObjectModel.from_dict(excludes_item_data)

                excludes.append(excludes_item)

        max_concurrent_machines_count = d.pop("maxConcurrentMachinesCount", UNSET)

        process_random_machines = d.pop("processRandomMachines", UNSET)

        max_random_machines_count = d.pop("maxRandomMachinesCount", UNSET)

        sure_backup_linked_jobs_model = cls(
            includes=includes,
            excludes=excludes,
            max_concurrent_machines_count=max_concurrent_machines_count,
            process_random_machines=process_random_machines,
            max_random_machines_count=max_random_machines_count,
        )

        sure_backup_linked_jobs_model.additional_properties = d
        return sure_backup_linked_jobs_model

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
