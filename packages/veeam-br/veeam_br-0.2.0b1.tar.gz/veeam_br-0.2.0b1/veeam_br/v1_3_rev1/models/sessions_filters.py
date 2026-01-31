from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_session_result import ESessionResult
from ..models.e_session_state import ESessionState
from ..models.e_session_type import ESessionType
from ..models.e_sessions_filters_order_column import ESessionsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionsFilters")


@_attrs_define
class SessionsFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ESessionsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        type_filter (list[ESessionType] | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (list[ESessionResult] | Unset):
        job_id_filter (UUID | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    created_after_filter: datetime.datetime | Unset = UNSET
    created_before_filter: datetime.datetime | Unset = UNSET
    ended_after_filter: datetime.datetime | Unset = UNSET
    ended_before_filter: datetime.datetime | Unset = UNSET
    type_filter: list[ESessionType] | Unset = UNSET
    state_filter: ESessionState | Unset = UNSET
    result_filter: list[ESessionResult] | Unset = UNSET
    job_id_filter: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        created_after_filter: str | Unset = UNSET
        if not isinstance(self.created_after_filter, Unset):
            created_after_filter = self.created_after_filter.isoformat()

        created_before_filter: str | Unset = UNSET
        if not isinstance(self.created_before_filter, Unset):
            created_before_filter = self.created_before_filter.isoformat()

        ended_after_filter: str | Unset = UNSET
        if not isinstance(self.ended_after_filter, Unset):
            ended_after_filter = self.ended_after_filter.isoformat()

        ended_before_filter: str | Unset = UNSET
        if not isinstance(self.ended_before_filter, Unset):
            ended_before_filter = self.ended_before_filter.isoformat()

        type_filter: list[str] | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = []
            for type_filter_item_data in self.type_filter:
                type_filter_item = type_filter_item_data.value
                type_filter.append(type_filter_item)

        state_filter: str | Unset = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

        result_filter: list[str] | Unset = UNSET
        if not isinstance(self.result_filter, Unset):
            result_filter = []
            for result_filter_item_data in self.result_filter:
                result_filter_item = result_filter_item_data.value
                result_filter.append(result_filter_item)

        job_id_filter: str | Unset = UNSET
        if not isinstance(self.job_id_filter, Unset):
            job_id_filter = str(self.job_id_filter)

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
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter
        if ended_after_filter is not UNSET:
            field_dict["endedAfterFilter"] = ended_after_filter
        if ended_before_filter is not UNSET:
            field_dict["endedBeforeFilter"] = ended_before_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if result_filter is not UNSET:
            field_dict["resultFilter"] = result_filter
        if job_id_filter is not UNSET:
            field_dict["jobIdFilter"] = job_id_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ESessionsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ESessionsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _created_after_filter = d.pop("createdAfterFilter", UNSET)
        created_after_filter: datetime.datetime | Unset
        if isinstance(_created_after_filter, Unset):
            created_after_filter = UNSET
        else:
            created_after_filter = isoparse(_created_after_filter)

        _created_before_filter = d.pop("createdBeforeFilter", UNSET)
        created_before_filter: datetime.datetime | Unset
        if isinstance(_created_before_filter, Unset):
            created_before_filter = UNSET
        else:
            created_before_filter = isoparse(_created_before_filter)

        _ended_after_filter = d.pop("endedAfterFilter", UNSET)
        ended_after_filter: datetime.datetime | Unset
        if isinstance(_ended_after_filter, Unset):
            ended_after_filter = UNSET
        else:
            ended_after_filter = isoparse(_ended_after_filter)

        _ended_before_filter = d.pop("endedBeforeFilter", UNSET)
        ended_before_filter: datetime.datetime | Unset
        if isinstance(_ended_before_filter, Unset):
            ended_before_filter = UNSET
        else:
            ended_before_filter = isoparse(_ended_before_filter)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[ESessionType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = ESessionType(type_filter_item_data)

                type_filter.append(type_filter_item)

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: ESessionState | Unset
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = ESessionState(_state_filter)

        _result_filter = d.pop("resultFilter", UNSET)
        result_filter: list[ESessionResult] | Unset = UNSET
        if _result_filter is not UNSET:
            result_filter = []
            for result_filter_item_data in _result_filter:
                result_filter_item = ESessionResult(result_filter_item_data)

                result_filter.append(result_filter_item)

        _job_id_filter = d.pop("jobIdFilter", UNSET)
        job_id_filter: UUID | Unset
        if isinstance(_job_id_filter, Unset):
            job_id_filter = UNSET
        else:
            job_id_filter = UUID(_job_id_filter)

        sessions_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            ended_after_filter=ended_after_filter,
            ended_before_filter=ended_before_filter,
            type_filter=type_filter,
            state_filter=state_filter,
            result_filter=result_filter,
            job_id_filter=job_id_filter,
        )

        sessions_filters.additional_properties = d
        return sessions_filters

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
