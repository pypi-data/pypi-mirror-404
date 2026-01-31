from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_suspicious_activity_events_filters_order_column import ESuspiciousActivityEventsFiltersOrderColumn
from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..models.e_suspicious_activity_source_type import ESuspiciousActivitySourceType
from ..models.e_suspicious_activity_state import ESuspiciousActivityState
from ..models.e_suspicious_activity_type import ESuspiciousActivityType
from ..types import UNSET, Unset

T = TypeVar("T", bound="SuspiciousActivityEventsFilters")


@_attrs_define
class SuspiciousActivityEventsFilters:
    """SuspiciousActivityEventsFilters

    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ESuspiciousActivityEventsFiltersOrderColumn | Unset): ESuspiciousActivityEventsFiltersOrderColumn.
        order_asc (bool | Unset):
        type_filter (ESuspiciousActivityType | Unset): Event type.
        detected_after_time_utc_filter (datetime.datetime | Unset):
        detected_before_time_utc_filter (datetime.datetime | Unset):
        backup_object_id_filter (UUID | Unset):
        state_filter (ESuspiciousActivityState | Unset): Event state.
        source_filter (ESuspiciousActivitySourceType | Unset): Event source type.
        severity_filter (ESuspiciousActivitySeverity | Unset): Malware status.
        created_by_filter (str | Unset):
        engine_filter (str | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ESuspiciousActivityEventsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    type_filter: ESuspiciousActivityType | Unset = UNSET
    detected_after_time_utc_filter: datetime.datetime | Unset = UNSET
    detected_before_time_utc_filter: datetime.datetime | Unset = UNSET
    backup_object_id_filter: UUID | Unset = UNSET
    state_filter: ESuspiciousActivityState | Unset = UNSET
    source_filter: ESuspiciousActivitySourceType | Unset = UNSET
    severity_filter: ESuspiciousActivitySeverity | Unset = UNSET
    created_by_filter: str | Unset = UNSET
    engine_filter: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        detected_after_time_utc_filter: str | Unset = UNSET
        if not isinstance(self.detected_after_time_utc_filter, Unset):
            detected_after_time_utc_filter = self.detected_after_time_utc_filter.isoformat()

        detected_before_time_utc_filter: str | Unset = UNSET
        if not isinstance(self.detected_before_time_utc_filter, Unset):
            detected_before_time_utc_filter = self.detected_before_time_utc_filter.isoformat()

        backup_object_id_filter: str | Unset = UNSET
        if not isinstance(self.backup_object_id_filter, Unset):
            backup_object_id_filter = str(self.backup_object_id_filter)

        state_filter: str | Unset = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

        source_filter: str | Unset = UNSET
        if not isinstance(self.source_filter, Unset):
            source_filter = self.source_filter.value

        severity_filter: str | Unset = UNSET
        if not isinstance(self.severity_filter, Unset):
            severity_filter = self.severity_filter.value

        created_by_filter = self.created_by_filter

        engine_filter = self.engine_filter

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
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if detected_after_time_utc_filter is not UNSET:
            field_dict["detectedAfterTimeUtcFilter"] = detected_after_time_utc_filter
        if detected_before_time_utc_filter is not UNSET:
            field_dict["detectedBeforeTimeUtcFilter"] = detected_before_time_utc_filter
        if backup_object_id_filter is not UNSET:
            field_dict["backupObjectIdFilter"] = backup_object_id_filter
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if source_filter is not UNSET:
            field_dict["sourceFilter"] = source_filter
        if severity_filter is not UNSET:
            field_dict["severityFilter"] = severity_filter
        if created_by_filter is not UNSET:
            field_dict["createdByFilter"] = created_by_filter
        if engine_filter is not UNSET:
            field_dict["engineFilter"] = engine_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ESuspiciousActivityEventsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ESuspiciousActivityEventsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: ESuspiciousActivityType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = ESuspiciousActivityType(_type_filter)

        _detected_after_time_utc_filter = d.pop("detectedAfterTimeUtcFilter", UNSET)
        detected_after_time_utc_filter: datetime.datetime | Unset
        if isinstance(_detected_after_time_utc_filter, Unset):
            detected_after_time_utc_filter = UNSET
        else:
            detected_after_time_utc_filter = isoparse(_detected_after_time_utc_filter)

        _detected_before_time_utc_filter = d.pop("detectedBeforeTimeUtcFilter", UNSET)
        detected_before_time_utc_filter: datetime.datetime | Unset
        if isinstance(_detected_before_time_utc_filter, Unset):
            detected_before_time_utc_filter = UNSET
        else:
            detected_before_time_utc_filter = isoparse(_detected_before_time_utc_filter)

        _backup_object_id_filter = d.pop("backupObjectIdFilter", UNSET)
        backup_object_id_filter: UUID | Unset
        if isinstance(_backup_object_id_filter, Unset):
            backup_object_id_filter = UNSET
        else:
            backup_object_id_filter = UUID(_backup_object_id_filter)

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: ESuspiciousActivityState | Unset
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = ESuspiciousActivityState(_state_filter)

        _source_filter = d.pop("sourceFilter", UNSET)
        source_filter: ESuspiciousActivitySourceType | Unset
        if isinstance(_source_filter, Unset):
            source_filter = UNSET
        else:
            source_filter = ESuspiciousActivitySourceType(_source_filter)

        _severity_filter = d.pop("severityFilter", UNSET)
        severity_filter: ESuspiciousActivitySeverity | Unset
        if isinstance(_severity_filter, Unset):
            severity_filter = UNSET
        else:
            severity_filter = ESuspiciousActivitySeverity(_severity_filter)

        created_by_filter = d.pop("createdByFilter", UNSET)

        engine_filter = d.pop("engineFilter", UNSET)

        suspicious_activity_events_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            type_filter=type_filter,
            detected_after_time_utc_filter=detected_after_time_utc_filter,
            detected_before_time_utc_filter=detected_before_time_utc_filter,
            backup_object_id_filter=backup_object_id_filter,
            state_filter=state_filter,
            source_filter=source_filter,
            severity_filter=severity_filter,
            created_by_filter=created_by_filter,
            engine_filter=engine_filter,
        )

        suspicious_activity_events_filters.additional_properties = d
        return suspicious_activity_events_filters

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
