from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.general_options_snmp_server_model import GeneralOptionsSNMPServerModel
    from ..models.general_options_syslog_event_filtering_model import GeneralOptionsSyslogEventFilteringModel
    from ..models.general_options_syslog_server_model import GeneralOptionsSyslogServerModel


T = TypeVar("T", bound="GeneralOptionsSiemIntegrationModel")


@_attrs_define
class GeneralOptionsSiemIntegrationModel:
    """SIEM integration settings.

    Attributes:
        snmp_events_enabled (bool): If `true`, SNMP trap management is enabled.
        syslog_events_enabled (bool): If `true`, syslog server integration is enabled.
        snmp_servers (list[GeneralOptionsSNMPServerModel] | Unset): Array of SNMP servers.
        syslog_server (GeneralOptionsSyslogServerModel | Unset): Syslog server settings.
        syslog_event_filtering (list[GeneralOptionsSyslogEventFilteringModel] | Unset): Array of syslog event filters.
    """

    snmp_events_enabled: bool
    syslog_events_enabled: bool
    snmp_servers: list[GeneralOptionsSNMPServerModel] | Unset = UNSET
    syslog_server: GeneralOptionsSyslogServerModel | Unset = UNSET
    syslog_event_filtering: list[GeneralOptionsSyslogEventFilteringModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        snmp_events_enabled = self.snmp_events_enabled

        syslog_events_enabled = self.syslog_events_enabled

        snmp_servers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.snmp_servers, Unset):
            snmp_servers = []
            for snmp_servers_item_data in self.snmp_servers:
                snmp_servers_item = snmp_servers_item_data.to_dict()
                snmp_servers.append(snmp_servers_item)

        syslog_server: dict[str, Any] | Unset = UNSET
        if not isinstance(self.syslog_server, Unset):
            syslog_server = self.syslog_server.to_dict()

        syslog_event_filtering: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.syslog_event_filtering, Unset):
            syslog_event_filtering = []
            for syslog_event_filtering_item_data in self.syslog_event_filtering:
                syslog_event_filtering_item = syslog_event_filtering_item_data.to_dict()
                syslog_event_filtering.append(syslog_event_filtering_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "SNMPEventsEnabled": snmp_events_enabled,
                "SyslogEventsEnabled": syslog_events_enabled,
            }
        )
        if snmp_servers is not UNSET:
            field_dict["SNMPServers"] = snmp_servers
        if syslog_server is not UNSET:
            field_dict["SyslogServer"] = syslog_server
        if syslog_event_filtering is not UNSET:
            field_dict["syslogEventFiltering"] = syslog_event_filtering

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.general_options_snmp_server_model import GeneralOptionsSNMPServerModel
        from ..models.general_options_syslog_event_filtering_model import GeneralOptionsSyslogEventFilteringModel
        from ..models.general_options_syslog_server_model import GeneralOptionsSyslogServerModel

        d = dict(src_dict)
        snmp_events_enabled = d.pop("SNMPEventsEnabled")

        syslog_events_enabled = d.pop("SyslogEventsEnabled")

        _snmp_servers = d.pop("SNMPServers", UNSET)
        snmp_servers: list[GeneralOptionsSNMPServerModel] | Unset = UNSET
        if _snmp_servers is not UNSET:
            snmp_servers = []
            for snmp_servers_item_data in _snmp_servers:
                snmp_servers_item = GeneralOptionsSNMPServerModel.from_dict(snmp_servers_item_data)

                snmp_servers.append(snmp_servers_item)

        _syslog_server = d.pop("SyslogServer", UNSET)
        syslog_server: GeneralOptionsSyslogServerModel | Unset
        if isinstance(_syslog_server, Unset):
            syslog_server = UNSET
        else:
            syslog_server = GeneralOptionsSyslogServerModel.from_dict(_syslog_server)

        _syslog_event_filtering = d.pop("syslogEventFiltering", UNSET)
        syslog_event_filtering: list[GeneralOptionsSyslogEventFilteringModel] | Unset = UNSET
        if _syslog_event_filtering is not UNSET:
            syslog_event_filtering = []
            for syslog_event_filtering_item_data in _syslog_event_filtering:
                syslog_event_filtering_item = GeneralOptionsSyslogEventFilteringModel.from_dict(
                    syslog_event_filtering_item_data
                )

                syslog_event_filtering.append(syslog_event_filtering_item)

        general_options_siem_integration_model = cls(
            snmp_events_enabled=snmp_events_enabled,
            syslog_events_enabled=syslog_events_enabled,
            snmp_servers=snmp_servers,
            syslog_server=syslog_server,
            syslog_event_filtering=syslog_event_filtering,
        )

        general_options_siem_integration_model.additional_properties = d
        return general_options_siem_integration_model

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
