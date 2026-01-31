from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunAfterJob")


@_attrs_define
class RunAfterJob:
    """Specifies that the job will run after another job.

    Attributes:
        job_name (str | Unset): Name of another job after which the job will run.
        job_id (UUID | Unset): ID of another job after which the job will run.
    """

    job_name: str | Unset = UNSET
    job_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_name = self.job_name

        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if job_name is not UNSET:
            field_dict["jobName"] = job_name
        if job_id is not UNSET:
            field_dict["jobId"] = job_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_name = d.pop("jobName", UNSET)

        _job_id = d.pop("jobId", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id, Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)

        run_after_job = cls(
            job_name=job_name,
            job_id=job_id,
        )

        run_after_job.additional_properties = d
        return run_after_job

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
