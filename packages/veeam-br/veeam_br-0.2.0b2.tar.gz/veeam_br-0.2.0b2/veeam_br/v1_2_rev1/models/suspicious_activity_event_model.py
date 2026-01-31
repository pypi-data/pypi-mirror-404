from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..models.e_suspicious_activity_source_type import ESuspiciousActivitySourceType
from ..models.e_suspicious_activity_state import ESuspiciousActivityState
from ..models.e_suspicious_activity_type import ESuspiciousActivityType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.suspicious_activity_machine_model import SuspiciousActivityMachineModel


T = TypeVar("T", bound="SuspiciousActivityEventModel")


@_attrs_define
class SuspiciousActivityEventModel:
    """Malware event.

    Attributes:
        id (UUID): ID of the event.
        type_ (ESuspiciousActivityType): Event type.
        detection_time_utc (datetime.datetime): Detection date and time, in UTC.
        state (ESuspiciousActivityState): Event state.
        details (str): Event description.
        source (ESuspiciousActivitySourceType): Event source type.
        severity (ESuspiciousActivitySeverity): Malware status.
        created_by (str): User account created the event.
        engine (str): Detection engine.
        machine (SuspiciousActivityMachineModel | Unset): Machine marked by the malware event.
    """

    id: UUID
    type_: ESuspiciousActivityType
    detection_time_utc: datetime.datetime
    state: ESuspiciousActivityState
    details: str
    source: ESuspiciousActivitySourceType
    severity: ESuspiciousActivitySeverity
    created_by: str
    engine: str
    machine: SuspiciousActivityMachineModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        detection_time_utc = self.detection_time_utc.isoformat()

        state = self.state.value

        details = self.details

        source = self.source.value

        severity = self.severity.value

        created_by = self.created_by

        engine = self.engine

        machine: dict[str, Any] | Unset = UNSET
        if not isinstance(self.machine, Unset):
            machine = self.machine.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "detectionTimeUtc": detection_time_utc,
                "state": state,
                "details": details,
                "source": source,
                "severity": severity,
                "createdBy": created_by,
                "engine": engine,
            }
        )
        if machine is not UNSET:
            field_dict["machine"] = machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.suspicious_activity_machine_model import SuspiciousActivityMachineModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ESuspiciousActivityType(d.pop("type"))

        detection_time_utc = isoparse(d.pop("detectionTimeUtc"))

        state = ESuspiciousActivityState(d.pop("state"))

        details = d.pop("details")

        source = ESuspiciousActivitySourceType(d.pop("source"))

        severity = ESuspiciousActivitySeverity(d.pop("severity"))

        created_by = d.pop("createdBy")

        engine = d.pop("engine")

        _machine = d.pop("machine", UNSET)
        machine: SuspiciousActivityMachineModel | Unset
        if isinstance(_machine, Unset):
            machine = UNSET
        else:
            machine = SuspiciousActivityMachineModel.from_dict(_machine)

        suspicious_activity_event_model = cls(
            id=id,
            type_=type_,
            detection_time_utc=detection_time_utc,
            state=state,
            details=details,
            source=source,
            severity=severity,
            created_by=created_by,
            engine=engine,
            machine=machine,
        )

        suspicious_activity_event_model.additional_properties = d
        return suspicious_activity_event_model

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
