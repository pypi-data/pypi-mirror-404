from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ServerTimeModel")


@_attrs_define
class ServerTimeModel:
    """Time settings of the backup server.

    Attributes:
        server_time (datetime.datetime): Current date and time on the backup server.
        time_zone (str | Unset): Time zone where the backup server is located.
    """

    server_time: datetime.datetime
    time_zone: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        server_time = self.server_time.isoformat()

        time_zone = self.time_zone

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serverTime": server_time,
            }
        )
        if time_zone is not UNSET:
            field_dict["timeZone"] = time_zone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        server_time = isoparse(d.pop("serverTime"))

        time_zone = d.pop("timeZone", UNSET)

        server_time_model = cls(
            server_time=server_time,
            time_zone=time_zone,
        )

        server_time_model.additional_properties = d
        return server_time_model

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
