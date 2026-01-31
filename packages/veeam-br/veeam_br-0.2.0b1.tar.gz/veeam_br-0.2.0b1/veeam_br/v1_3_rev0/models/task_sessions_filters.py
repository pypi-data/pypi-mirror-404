from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_antivirus_scan_result import EAntivirusScanResult
from ..models.e_antivirus_scan_state import EAntivirusScanState
from ..models.e_antivirus_scan_type import EAntivirusScanType
from ..models.e_session_result import ESessionResult
from ..models.e_session_state import ESessionState
from ..models.e_session_type import ESessionType
from ..models.e_task_session_type import ETaskSessionType
from ..models.e_task_sessions_filters_order_column import ETaskSessionsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="TaskSessionsFilters")


@_attrs_define
class TaskSessionsFilters:
    """
    Attributes:
        skip (int | Unset): Number of task sessions to skip.
        limit (int | Unset): Maximum number of task sessions to return.
        order_column (ETaskSessionsFiltersOrderColumn | Unset): Sorts task sessions according to one of the parameters.
        order_asc (bool | Unset): If `true`, sorts task sessions in the ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters sessions by the `nameFilter` pattern. The pattern can match any session
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        type_filter (ETaskSessionType | Unset): Task session type.
        session_type_filter (ESessionType | Unset): Type of the session.
        created_after_filter (datetime.datetime | Unset): Returns task sessions that are created after the specified
            date and time.
        created_before_filter (datetime.datetime | Unset): Returns task sessions created before the specified date and
            time.
        ended_after_filter (datetime.datetime | Unset): Returns task sessions that finished after the specified date and
            time.
        ended_before_filter (datetime.datetime | Unset): Returns task sessions that finished before the specified date
            and time.
        state_filter (ESessionState | Unset): State of the session.
        result_filter (ESessionResult | Unset): Result status.
        scan_type_filter (EAntivirusScanType | Unset): Type of antivirus scan.
        scan_result_filter (EAntivirusScanResult | Unset): Antivirus scan result.
        scan_state_filter (EAntivirusScanState | Unset): State of the antivirus scan.
        session_id_filter (UUID | Unset): Returns the task sessions with the specified session ID.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: ETaskSessionType | Unset = UNSET
    session_type_filter: ESessionType | Unset = UNSET
    created_after_filter: datetime.datetime | Unset = UNSET
    created_before_filter: datetime.datetime | Unset = UNSET
    ended_after_filter: datetime.datetime | Unset = UNSET
    ended_before_filter: datetime.datetime | Unset = UNSET
    state_filter: ESessionState | Unset = UNSET
    result_filter: ESessionResult | Unset = UNSET
    scan_type_filter: EAntivirusScanType | Unset = UNSET
    scan_result_filter: EAntivirusScanResult | Unset = UNSET
    scan_state_filter: EAntivirusScanState | Unset = UNSET
    session_id_filter: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        session_type_filter: str | Unset = UNSET
        if not isinstance(self.session_type_filter, Unset):
            session_type_filter = self.session_type_filter.value

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

        state_filter: str | Unset = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

        result_filter: str | Unset = UNSET
        if not isinstance(self.result_filter, Unset):
            result_filter = self.result_filter.value

        scan_type_filter: str | Unset = UNSET
        if not isinstance(self.scan_type_filter, Unset):
            scan_type_filter = self.scan_type_filter.value

        scan_result_filter: str | Unset = UNSET
        if not isinstance(self.scan_result_filter, Unset):
            scan_result_filter = self.scan_result_filter.value

        scan_state_filter: str | Unset = UNSET
        if not isinstance(self.scan_state_filter, Unset):
            scan_state_filter = self.scan_state_filter.value

        session_id_filter: str | Unset = UNSET
        if not isinstance(self.session_id_filter, Unset):
            session_id_filter = str(self.session_id_filter)

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
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if session_type_filter is not UNSET:
            field_dict["sessionTypeFilter"] = session_type_filter
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter
        if ended_after_filter is not UNSET:
            field_dict["endedAfterFilter"] = ended_after_filter
        if ended_before_filter is not UNSET:
            field_dict["endedBeforeFilter"] = ended_before_filter
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if result_filter is not UNSET:
            field_dict["resultFilter"] = result_filter
        if scan_type_filter is not UNSET:
            field_dict["scanTypeFilter"] = scan_type_filter
        if scan_result_filter is not UNSET:
            field_dict["scanResultFilter"] = scan_result_filter
        if scan_state_filter is not UNSET:
            field_dict["scanStateFilter"] = scan_state_filter
        if session_id_filter is not UNSET:
            field_dict["sessionIdFilter"] = session_id_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ETaskSessionsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ETaskSessionsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: ETaskSessionType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = ETaskSessionType(_type_filter)

        _session_type_filter = d.pop("sessionTypeFilter", UNSET)
        session_type_filter: ESessionType | Unset
        if isinstance(_session_type_filter, Unset):
            session_type_filter = UNSET
        else:
            session_type_filter = ESessionType(_session_type_filter)

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

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: ESessionState | Unset
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = ESessionState(_state_filter)

        _result_filter = d.pop("resultFilter", UNSET)
        result_filter: ESessionResult | Unset
        if isinstance(_result_filter, Unset):
            result_filter = UNSET
        else:
            result_filter = ESessionResult(_result_filter)

        _scan_type_filter = d.pop("scanTypeFilter", UNSET)
        scan_type_filter: EAntivirusScanType | Unset
        if isinstance(_scan_type_filter, Unset):
            scan_type_filter = UNSET
        else:
            scan_type_filter = EAntivirusScanType(_scan_type_filter)

        _scan_result_filter = d.pop("scanResultFilter", UNSET)
        scan_result_filter: EAntivirusScanResult | Unset
        if isinstance(_scan_result_filter, Unset):
            scan_result_filter = UNSET
        else:
            scan_result_filter = EAntivirusScanResult(_scan_result_filter)

        _scan_state_filter = d.pop("scanStateFilter", UNSET)
        scan_state_filter: EAntivirusScanState | Unset
        if isinstance(_scan_state_filter, Unset):
            scan_state_filter = UNSET
        else:
            scan_state_filter = EAntivirusScanState(_scan_state_filter)

        _session_id_filter = d.pop("sessionIdFilter", UNSET)
        session_id_filter: UUID | Unset
        if isinstance(_session_id_filter, Unset):
            session_id_filter = UNSET
        else:
            session_id_filter = UUID(_session_id_filter)

        task_sessions_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            session_type_filter=session_type_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            ended_after_filter=ended_after_filter,
            ended_before_filter=ended_before_filter,
            state_filter=state_filter,
            result_filter=result_filter,
            scan_type_filter=scan_type_filter,
            scan_result_filter=scan_result_filter,
            scan_state_filter=scan_state_filter,
            session_id_filter=session_id_filter,
        )

        task_sessions_filters.additional_properties = d
        return task_sessions_filters

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
