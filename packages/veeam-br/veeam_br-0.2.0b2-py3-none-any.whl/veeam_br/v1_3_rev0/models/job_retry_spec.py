from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobRetrySpec")


@_attrs_define
class JobRetrySpec:
    """Job retry settings.

    Attributes:
        start_chained_jobs (bool | Unset): If `true`, Veeam Backup & Replication will start chained jobs as well.
            Default: False.
    """

    start_chained_jobs: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start_chained_jobs = self.start_chained_jobs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if start_chained_jobs is not UNSET:
            field_dict["startChainedJobs"] = start_chained_jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_chained_jobs = d.pop("startChainedJobs", UNSET)

        job_retry_spec = cls(
            start_chained_jobs=start_chained_jobs,
        )

        job_retry_spec.additional_properties = d
        return job_retry_spec

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
