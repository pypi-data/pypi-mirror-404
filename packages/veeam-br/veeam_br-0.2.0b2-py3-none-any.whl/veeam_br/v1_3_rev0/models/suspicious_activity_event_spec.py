from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_creating_suspicious_activity_severity import ECreatingSuspiciousActivitySeverity
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.suspicious_activity_machine_spec import SuspiciousActivityMachineSpec


T = TypeVar("T", bound="SuspiciousActivityEventSpec")


@_attrs_define
class SuspiciousActivityEventSpec:
    """SuspiciousActivityInfo

    Attributes:
        detection_time_utc (datetime.datetime): Detection date and time, in UTC.
        machine (SuspiciousActivityMachineSpec): Machine that you want to mark with the malware event. Specify at least
            2 parameters.<p> Note that Veeam Backup & Replication can identify a machine by its FQDN, IPv4 address and IPv6
            address only if the machine has been powered on during the backup. If you back up a powered-off machine, Veeam
            Backup & Replication will not get the machine IP addresses and domain name and will not be able to identify the
            machine.</p>
        details (str): Event description.
        engine (str): Detection engine.
        severity (ECreatingSuspiciousActivitySeverity | Unset): Malware status enum for creating suspicious activity
            operation.
    """

    detection_time_utc: datetime.datetime
    machine: SuspiciousActivityMachineSpec
    details: str
    engine: str
    severity: ECreatingSuspiciousActivitySeverity | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        detection_time_utc = self.detection_time_utc.isoformat()

        machine = self.machine.to_dict()

        details = self.details

        engine = self.engine

        severity: str | Unset = UNSET
        if not isinstance(self.severity, Unset):
            severity = self.severity.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detectionTimeUtc": detection_time_utc,
                "machine": machine,
                "details": details,
                "engine": engine,
            }
        )
        if severity is not UNSET:
            field_dict["severity"] = severity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.suspicious_activity_machine_spec import SuspiciousActivityMachineSpec

        d = dict(src_dict)
        detection_time_utc = isoparse(d.pop("detectionTimeUtc"))

        machine = SuspiciousActivityMachineSpec.from_dict(d.pop("machine"))

        details = d.pop("details")

        engine = d.pop("engine")

        _severity = d.pop("severity", UNSET)
        severity: ECreatingSuspiciousActivitySeverity | Unset
        if isinstance(_severity, Unset):
            severity = UNSET
        else:
            severity = ECreatingSuspiciousActivitySeverity(_severity)

        suspicious_activity_event_spec = cls(
            detection_time_utc=detection_time_utc,
            machine=machine,
            details=details,
            engine=engine,
            severity=severity,
        )

        suspicious_activity_event_spec.additional_properties = d
        return suspicious_activity_event_spec

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
