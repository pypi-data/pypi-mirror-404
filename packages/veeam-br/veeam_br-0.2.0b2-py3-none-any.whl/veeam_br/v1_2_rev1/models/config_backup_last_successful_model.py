from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfigBackupLastSuccessfulModel")


@_attrs_define
class ConfigBackupLastSuccessfulModel:
    """Last successful backup.

    Attributes:
        last_successful_time (datetime.datetime | Unset): Date and time when the last successful backup was created.
        session_id (UUID | Unset): ID of the job session.
    """

    last_successful_time: datetime.datetime | Unset = UNSET
    session_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        last_successful_time: str | Unset = UNSET
        if not isinstance(self.last_successful_time, Unset):
            last_successful_time = self.last_successful_time.isoformat()

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if last_successful_time is not UNSET:
            field_dict["lastSuccessfulTime"] = last_successful_time
        if session_id is not UNSET:
            field_dict["sessionId"] = session_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _last_successful_time = d.pop("lastSuccessfulTime", UNSET)
        last_successful_time: datetime.datetime | Unset
        if isinstance(_last_successful_time, Unset):
            last_successful_time = UNSET
        else:
            last_successful_time = isoparse(_last_successful_time)

        _session_id = d.pop("sessionId", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        config_backup_last_successful_model = cls(
            last_successful_time=last_successful_time,
            session_id=session_id,
        )

        config_backup_last_successful_model.additional_properties = d
        return config_backup_last_successful_model

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
