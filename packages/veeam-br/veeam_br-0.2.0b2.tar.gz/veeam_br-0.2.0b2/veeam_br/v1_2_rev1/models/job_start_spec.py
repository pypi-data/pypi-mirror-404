from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStartSpec")


@_attrs_define
class JobStartSpec:
    """
    Attributes:
        perform_active_full (bool): If `true`, Veeam Backup & Replication will perform an active full backup. Default:
            False.
        start_chained_jobs (bool | Unset): If `true`, Veeam Backup & Replication will start chained jobs as well.
            Default: False.
    """

    perform_active_full: bool = False
    start_chained_jobs: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        perform_active_full = self.perform_active_full

        start_chained_jobs = self.start_chained_jobs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "performActiveFull": perform_active_full,
            }
        )
        if start_chained_jobs is not UNSET:
            field_dict["startChainedJobs"] = start_chained_jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        perform_active_full = d.pop("performActiveFull")

        start_chained_jobs = d.pop("startChainedJobs", UNSET)

        job_start_spec = cls(
            perform_active_full=perform_active_full,
            start_chained_jobs=start_chained_jobs,
        )

        job_start_spec.additional_properties = d
        return job_start_spec

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
