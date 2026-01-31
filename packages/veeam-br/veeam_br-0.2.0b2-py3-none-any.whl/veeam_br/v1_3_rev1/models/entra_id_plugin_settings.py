from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIDPluginSettings")


@_attrs_define
class EntraIDPluginSettings:
    """Settings for Microsoft Entra ID plug-in.

    Attributes:
        max_parallel_jobs_per_worker (int): Maximum number of parallel backup requests for the backup server.
        storage_queue_capacity (int): Storage queue capacity.
    """

    max_parallel_jobs_per_worker: int
    storage_queue_capacity: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        max_parallel_jobs_per_worker = self.max_parallel_jobs_per_worker

        storage_queue_capacity = self.storage_queue_capacity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "maxParallelJobsPerWorker": max_parallel_jobs_per_worker,
                "storageQueueCapacity": storage_queue_capacity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        max_parallel_jobs_per_worker = d.pop("maxParallelJobsPerWorker")

        storage_queue_capacity = d.pop("storageQueueCapacity")

        entra_id_plugin_settings = cls(
            max_parallel_jobs_per_worker=max_parallel_jobs_per_worker,
            storage_queue_capacity=storage_queue_capacity,
        )

        entra_id_plugin_settings.additional_properties = d
        return entra_id_plugin_settings

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
