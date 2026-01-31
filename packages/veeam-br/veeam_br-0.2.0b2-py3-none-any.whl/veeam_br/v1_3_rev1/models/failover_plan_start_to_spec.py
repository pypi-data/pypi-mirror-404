from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="FailoverPlanStartToSpec")


@_attrs_define
class FailoverPlanStartToSpec:
    """Starting failover to specific restore point.

    Attributes:
        time_period (datetime.datetime | Unset): Date and time to which you want to fail over. Veeam Backup &
            Replication will find a restore point closest to this moment.
    """

    time_period: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        time_period: str | Unset = UNSET
        if not isinstance(self.time_period, Unset):
            time_period = self.time_period.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if time_period is not UNSET:
            field_dict["timePeriod"] = time_period

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _time_period = d.pop("timePeriod", UNSET)
        time_period: datetime.datetime | Unset
        if isinstance(_time_period, Unset):
            time_period = UNSET
        else:
            time_period = isoparse(_time_period)

        failover_plan_start_to_spec = cls(
            time_period=time_period,
        )

        failover_plan_start_to_spec.additional_properties = d
        return failover_plan_start_to_spec

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
