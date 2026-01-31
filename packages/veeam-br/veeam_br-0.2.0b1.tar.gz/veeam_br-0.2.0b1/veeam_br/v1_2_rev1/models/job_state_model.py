from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_job_status import EJobStatus
from ..models.e_job_type import EJobType
from ..models.e_job_workload import EJobWorkload
from ..models.e_session_result import ESessionResult
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStateModel")


@_attrs_define
class JobStateModel:
    """
    Attributes:
        id (UUID): ID of the job.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        status (EJobStatus): Current status of the job.
        last_result (ESessionResult): Result status.
        workload (EJobWorkload): Workload which the job must process.
        objects_count (int): Number of objects processed by the job.
        last_run (datetime.datetime | Unset): Last run of the job.
        next_run (datetime.datetime | Unset): Next run of the job.
        repository_id (UUID | Unset): ID of the backup repository.
        repository_name (str | Unset): Name of the backup repository.
        session_id (UUID | Unset): ID of the last job session.
    """

    id: UUID
    name: str
    type_: EJobType
    description: str
    status: EJobStatus
    last_result: ESessionResult
    workload: EJobWorkload
    objects_count: int
    last_run: datetime.datetime | Unset = UNSET
    next_run: datetime.datetime | Unset = UNSET
    repository_id: UUID | Unset = UNSET
    repository_name: str | Unset = UNSET
    session_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        description = self.description

        status = self.status.value

        last_result = self.last_result.value

        workload = self.workload.value

        objects_count = self.objects_count

        last_run: str | Unset = UNSET
        if not isinstance(self.last_run, Unset):
            last_run = self.last_run.isoformat()

        next_run: str | Unset = UNSET
        if not isinstance(self.next_run, Unset):
            next_run = self.next_run.isoformat()

        repository_id: str | Unset = UNSET
        if not isinstance(self.repository_id, Unset):
            repository_id = str(self.repository_id)

        repository_name = self.repository_name

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "description": description,
                "status": status,
                "lastResult": last_result,
                "workload": workload,
                "objectsCount": objects_count,
            }
        )
        if last_run is not UNSET:
            field_dict["lastRun"] = last_run
        if next_run is not UNSET:
            field_dict["nextRun"] = next_run
        if repository_id is not UNSET:
            field_dict["repositoryId"] = repository_id
        if repository_name is not UNSET:
            field_dict["repositoryName"] = repository_name
        if session_id is not UNSET:
            field_dict["sessionId"] = session_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        status = EJobStatus(d.pop("status"))

        last_result = ESessionResult(d.pop("lastResult"))

        workload = EJobWorkload(d.pop("workload"))

        objects_count = d.pop("objectsCount")

        _last_run = d.pop("lastRun", UNSET)
        last_run: datetime.datetime | Unset
        if isinstance(_last_run, Unset):
            last_run = UNSET
        else:
            last_run = isoparse(_last_run)

        _next_run = d.pop("nextRun", UNSET)
        next_run: datetime.datetime | Unset
        if isinstance(_next_run, Unset):
            next_run = UNSET
        else:
            next_run = isoparse(_next_run)

        _repository_id = d.pop("repositoryId", UNSET)
        repository_id: UUID | Unset
        if isinstance(_repository_id, Unset):
            repository_id = UNSET
        else:
            repository_id = UUID(_repository_id)

        repository_name = d.pop("repositoryName", UNSET)

        _session_id = d.pop("sessionId", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        job_state_model = cls(
            id=id,
            name=name,
            type_=type_,
            description=description,
            status=status,
            last_result=last_result,
            workload=workload,
            objects_count=objects_count,
            last_run=last_run,
            next_run=next_run,
            repository_id=repository_id,
            repository_name=repository_name,
            session_id=session_id,
        )

        job_state_model.additional_properties = d
        return job_state_model

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
