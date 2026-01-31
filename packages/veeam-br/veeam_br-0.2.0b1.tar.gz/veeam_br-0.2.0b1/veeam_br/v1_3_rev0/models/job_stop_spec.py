from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStopSpec")


@_attrs_define
class JobStopSpec:
    """Job stop settings.

    Attributes:
        graceful_stop (bool): If `true`, Veeam Backup & Replication will produce a new restore point for those VMs that
            have already been processed and for VMs that are being processed at the moment. Default: True.
        cancel_chained_jobs (bool | Unset): If `true`, Veeam Backup & Replication will cancel chained jobs. Default:
            False.
    """

    graceful_stop: bool = True
    cancel_chained_jobs: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        graceful_stop = self.graceful_stop

        cancel_chained_jobs = self.cancel_chained_jobs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "gracefulStop": graceful_stop,
            }
        )
        if cancel_chained_jobs is not UNSET:
            field_dict["cancelChainedJobs"] = cancel_chained_jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        graceful_stop = d.pop("gracefulStop")

        cancel_chained_jobs = d.pop("cancelChainedJobs", UNSET)

        job_stop_spec = cls(
            graceful_stop=graceful_stop,
            cancel_chained_jobs=cancel_chained_jobs,
        )

        job_stop_spec.additional_properties = d
        return job_stop_spec

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
