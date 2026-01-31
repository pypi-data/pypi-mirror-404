from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_task_log_record_status import ETaskLogRecordStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionLogRecordModel")


@_attrs_define
class SessionLogRecordModel:
    """Log record of the session.

    Attributes:
        id (int | Unset): ID of the log record.
        status (ETaskLogRecordStatus | Unset): Status of the log record.
        start_time (datetime.datetime | Unset): Date and time when the operation was started.
        update_time (datetime.datetime | Unset): Date and time when the log record was updated.
        title (str | Unset): Title of the log record.
        description (str | Unset): Description of the log record.
        additional_info (str | Unset): Additional information of the log record.
    """

    id: int | Unset = UNSET
    status: ETaskLogRecordStatus | Unset = UNSET
    start_time: datetime.datetime | Unset = UNSET
    update_time: datetime.datetime | Unset = UNSET
    title: str | Unset = UNSET
    description: str | Unset = UNSET
    additional_info: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        start_time: str | Unset = UNSET
        if not isinstance(self.start_time, Unset):
            start_time = self.start_time.isoformat()

        update_time: str | Unset = UNSET
        if not isinstance(self.update_time, Unset):
            update_time = self.update_time.isoformat()

        title = self.title

        description = self.description

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status
        if start_time is not UNSET:
            field_dict["startTime"] = start_time
        if update_time is not UNSET:
            field_dict["updateTime"] = update_time
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if additional_info is not UNSET:
            field_dict["additionalInfo"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _status = d.pop("status", UNSET)
        status: ETaskLogRecordStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ETaskLogRecordStatus(_status)

        _start_time = d.pop("startTime", UNSET)
        start_time: datetime.datetime | Unset
        if isinstance(_start_time, Unset):
            start_time = UNSET
        else:
            start_time = isoparse(_start_time)

        _update_time = d.pop("updateTime", UNSET)
        update_time: datetime.datetime | Unset
        if isinstance(_update_time, Unset):
            update_time = UNSET
        else:
            update_time = isoparse(_update_time)

        title = d.pop("title", UNSET)

        description = d.pop("description", UNSET)

        additional_info = d.pop("additionalInfo", UNSET)

        session_log_record_model = cls(
            id=id,
            status=status,
            start_time=start_time,
            update_time=update_time,
            title=title,
            description=description,
            additional_info=additional_info,
        )

        session_log_record_model.additional_properties = d
        return session_log_record_model

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
