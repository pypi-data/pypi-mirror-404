from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_unstructured_data_instant_recovery_switchover_type import EUnstructuredDataInstantRecoverySwitchoverType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataSwitchoverSettingsModel")


@_attrs_define
class UnstructuredDataSwitchoverSettingsModel:
    """Switchover settings for Instant File Share Recovery.

    Attributes:
        type_ (EUnstructuredDataInstantRecoverySwitchoverType): Switchover type.
        schedule_time (datetime.datetime | Unset): Date and time when switchover will be triggered.
    """

    type_: EUnstructuredDataInstantRecoverySwitchoverType
    schedule_time: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        schedule_time: str | Unset = UNSET
        if not isinstance(self.schedule_time, Unset):
            schedule_time = self.schedule_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if schedule_time is not UNSET:
            field_dict["scheduleTime"] = schedule_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EUnstructuredDataInstantRecoverySwitchoverType(d.pop("type"))

        _schedule_time = d.pop("scheduleTime", UNSET)
        schedule_time: datetime.datetime | Unset
        if isinstance(_schedule_time, Unset):
            schedule_time = UNSET
        else:
            schedule_time = isoparse(_schedule_time)

        unstructured_data_switchover_settings_model = cls(
            type_=type_,
            schedule_time=schedule_time,
        )

        unstructured_data_switchover_settings_model.additional_properties = d
        return unstructured_data_switchover_settings_model

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
