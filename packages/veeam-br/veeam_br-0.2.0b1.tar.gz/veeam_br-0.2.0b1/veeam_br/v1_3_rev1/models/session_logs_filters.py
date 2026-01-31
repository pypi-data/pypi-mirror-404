from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_task_log_record_status import ETaskLogRecordStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionLogsFilters")


@_attrs_define
class SessionLogsFilters:
    """
    Attributes:
        status_filter (ETaskLogRecordStatus | Unset): Status of the log record.
    """

    status_filter: ETaskLogRecordStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status_filter: str | Unset = UNSET
        if not isinstance(self.status_filter, Unset):
            status_filter = self.status_filter.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status_filter is not UNSET:
            field_dict["statusFilter"] = status_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _status_filter = d.pop("statusFilter", UNSET)
        status_filter: ETaskLogRecordStatus | Unset
        if isinstance(_status_filter, Unset):
            status_filter = UNSET
        else:
            status_filter = ETaskLogRecordStatus(_status_filter)

        session_logs_filters = cls(
            status_filter=status_filter,
        )

        session_logs_filters.additional_properties = d
        return session_logs_filters

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
