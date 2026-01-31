from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_syslog_event_severity import ESyslogEventSeverity

T = TypeVar("T", bound="GeneralOptionsSyslogEventFilteringModel")


@_attrs_define
class GeneralOptionsSyslogEventFilteringModel:
    """
    Attributes:
        event_id (str): Event ID. For a complete list of Veeam Backup & Replication events, see the [Event IDs
            List](https://helpcenter.veeam.com/docs/vbr/events/event_id_list.html?ver=13) section of the Event Reference
            User Guide.
        severity (list[ESyslogEventSeverity]): Array of event severity levels. Each entry prevents Veeam Backup &
            Replication from sending events of the specified severity level to the syslog server.
    """

    event_id: str
    severity: list[ESyslogEventSeverity]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_id = self.event_id

        severity = []
        for severity_item_data in self.severity:
            severity_item = severity_item_data.value
            severity.append(severity_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eventId": event_id,
                "severity": severity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        event_id = d.pop("eventId")

        severity = []
        _severity = d.pop("severity")
        for severity_item_data in _severity:
            severity_item = ESyslogEventSeverity(severity_item_data)

            severity.append(severity_item)

        general_options_syslog_event_filtering_model = cls(
            event_id=event_id,
            severity=severity,
        )

        general_options_syslog_event_filtering_model.additional_properties = d
        return general_options_syslog_event_filtering_model

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
