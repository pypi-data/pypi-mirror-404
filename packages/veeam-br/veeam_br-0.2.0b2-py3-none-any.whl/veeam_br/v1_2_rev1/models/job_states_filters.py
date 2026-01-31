from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_job_states_filters_order_column import EJobStatesFiltersOrderColumn
from ..models.e_job_status import EJobStatus
from ..models.e_job_type import EJobType
from ..models.e_job_workload import EJobWorkload
from ..models.e_session_result import ESessionResult
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStatesFilters")


@_attrs_define
class JobStatesFilters:
    """Filters jobs by the specified parameters.

    Attributes:
        skip (int | Unset): Skips the specified number of jobs.
        limit (int | Unset): Returns the specified number of jobs.
        order_column (EJobStatesFiltersOrderColumn | Unset): Orders job states by the specified column.
        order_asc (bool | Unset): If `true`, sorts jobs in the ascending order by the `orderColumn` parameter.
        id_filter (UUID | Unset):
        name_filter (str | Unset): Filters jobs by the `nameFilter` pattern. The pattern can match any job state
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        type_filter (EJobType | Unset): Type of the job.
        last_result_filter (ESessionResult | Unset): Result status.
        status_filter (EJobStatus | Unset): Current status of the job.
        workload_filter (EJobWorkload | Unset): Workload which the job must process.
        last_run_after_filter (datetime.datetime | Unset):
        last_run_before_filter (datetime.datetime | Unset):
        is_high_priority_job_filter (bool | Unset): If `true`, returns job states for high priority jobs only.
        repository_id_filter (UUID | Unset):
        objects_count_filter (int | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    id_filter: UUID | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: EJobType | Unset = UNSET
    last_result_filter: ESessionResult | Unset = UNSET
    status_filter: EJobStatus | Unset = UNSET
    workload_filter: EJobWorkload | Unset = UNSET
    last_run_after_filter: datetime.datetime | Unset = UNSET
    last_run_before_filter: datetime.datetime | Unset = UNSET
    is_high_priority_job_filter: bool | Unset = UNSET
    repository_id_filter: UUID | Unset = UNSET
    objects_count_filter: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        id_filter: str | Unset = UNSET
        if not isinstance(self.id_filter, Unset):
            id_filter = str(self.id_filter)

        name_filter = self.name_filter

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        last_result_filter: str | Unset = UNSET
        if not isinstance(self.last_result_filter, Unset):
            last_result_filter = self.last_result_filter.value

        status_filter: str | Unset = UNSET
        if not isinstance(self.status_filter, Unset):
            status_filter = self.status_filter.value

        workload_filter: str | Unset = UNSET
        if not isinstance(self.workload_filter, Unset):
            workload_filter = self.workload_filter.value

        last_run_after_filter: str | Unset = UNSET
        if not isinstance(self.last_run_after_filter, Unset):
            last_run_after_filter = self.last_run_after_filter.isoformat()

        last_run_before_filter: str | Unset = UNSET
        if not isinstance(self.last_run_before_filter, Unset):
            last_run_before_filter = self.last_run_before_filter.isoformat()

        is_high_priority_job_filter = self.is_high_priority_job_filter

        repository_id_filter: str | Unset = UNSET
        if not isinstance(self.repository_id_filter, Unset):
            repository_id_filter = str(self.repository_id_filter)

        objects_count_filter = self.objects_count_filter

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit
        if order_column is not UNSET:
            field_dict["orderColumn"] = order_column
        if order_asc is not UNSET:
            field_dict["orderAsc"] = order_asc
        if id_filter is not UNSET:
            field_dict["idFilter"] = id_filter
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if last_result_filter is not UNSET:
            field_dict["lastResultFilter"] = last_result_filter
        if status_filter is not UNSET:
            field_dict["statusFilter"] = status_filter
        if workload_filter is not UNSET:
            field_dict["workloadFilter"] = workload_filter
        if last_run_after_filter is not UNSET:
            field_dict["lastRunAfterFilter"] = last_run_after_filter
        if last_run_before_filter is not UNSET:
            field_dict["lastRunBeforeFilter"] = last_run_before_filter
        if is_high_priority_job_filter is not UNSET:
            field_dict["isHighPriorityJobFilter"] = is_high_priority_job_filter
        if repository_id_filter is not UNSET:
            field_dict["repositoryIdFilter"] = repository_id_filter
        if objects_count_filter is not UNSET:
            field_dict["objectsCountFilter"] = objects_count_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EJobStatesFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EJobStatesFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _id_filter = d.pop("idFilter", UNSET)
        id_filter: UUID | Unset
        if isinstance(_id_filter, Unset):
            id_filter = UNSET
        else:
            id_filter = UUID(_id_filter)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: EJobType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = EJobType(_type_filter)

        _last_result_filter = d.pop("lastResultFilter", UNSET)
        last_result_filter: ESessionResult | Unset
        if isinstance(_last_result_filter, Unset):
            last_result_filter = UNSET
        else:
            last_result_filter = ESessionResult(_last_result_filter)

        _status_filter = d.pop("statusFilter", UNSET)
        status_filter: EJobStatus | Unset
        if isinstance(_status_filter, Unset):
            status_filter = UNSET
        else:
            status_filter = EJobStatus(_status_filter)

        _workload_filter = d.pop("workloadFilter", UNSET)
        workload_filter: EJobWorkload | Unset
        if isinstance(_workload_filter, Unset):
            workload_filter = UNSET
        else:
            workload_filter = EJobWorkload(_workload_filter)

        _last_run_after_filter = d.pop("lastRunAfterFilter", UNSET)
        last_run_after_filter: datetime.datetime | Unset
        if isinstance(_last_run_after_filter, Unset):
            last_run_after_filter = UNSET
        else:
            last_run_after_filter = isoparse(_last_run_after_filter)

        _last_run_before_filter = d.pop("lastRunBeforeFilter", UNSET)
        last_run_before_filter: datetime.datetime | Unset
        if isinstance(_last_run_before_filter, Unset):
            last_run_before_filter = UNSET
        else:
            last_run_before_filter = isoparse(_last_run_before_filter)

        is_high_priority_job_filter = d.pop("isHighPriorityJobFilter", UNSET)

        _repository_id_filter = d.pop("repositoryIdFilter", UNSET)
        repository_id_filter: UUID | Unset
        if isinstance(_repository_id_filter, Unset):
            repository_id_filter = UNSET
        else:
            repository_id_filter = UUID(_repository_id_filter)

        objects_count_filter = d.pop("objectsCountFilter", UNSET)

        job_states_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            id_filter=id_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            last_result_filter=last_result_filter,
            status_filter=status_filter,
            workload_filter=workload_filter,
            last_run_after_filter=last_run_after_filter,
            last_run_before_filter=last_run_before_filter,
            is_high_priority_job_filter=is_high_priority_job_filter,
            repository_id_filter=repository_id_filter,
            objects_count_filter=objects_count_filter,
        )

        job_states_filters.additional_properties = d
        return job_states_filters

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
