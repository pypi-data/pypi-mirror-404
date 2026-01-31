from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_failback_mode_type import EFailbackModeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ReplicaFailbackModeSpec")


@_attrs_define
class ReplicaFailbackModeSpec:
    """Failback mode.

    Attributes:
        type_ (EFailbackModeType | Unset): Failback mode type.
        scheduled_time (datetime.datetime | Unset): Date and time when switchover to production must be performed (for
            scheduled mode).
    """

    type_: EFailbackModeType | Unset = UNSET
    scheduled_time: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        scheduled_time: str | Unset = UNSET
        if not isinstance(self.scheduled_time, Unset):
            scheduled_time = self.scheduled_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if scheduled_time is not UNSET:
            field_dict["scheduledTime"] = scheduled_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: EFailbackModeType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EFailbackModeType(_type_)

        _scheduled_time = d.pop("scheduledTime", UNSET)
        scheduled_time: datetime.datetime | Unset
        if isinstance(_scheduled_time, Unset):
            scheduled_time = UNSET
        else:
            scheduled_time = isoparse(_scheduled_time)

        replica_failback_mode_spec = cls(
            type_=type_,
            scheduled_time=scheduled_time,
        )

        replica_failback_mode_spec.additional_properties = d
        return replica_failback_mode_spec

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
