from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_syslog_server_protocol import ESyslogServerProtocol
from ..types import UNSET, Unset

T = TypeVar("T", bound="GeneralOptionsSyslogServerModel")


@_attrs_define
class GeneralOptionsSyslogServerModel:
    """Syslog server settings.

    Attributes:
        server_name (str): Full DNS name or IP address of the syslog server.
        port (int | Unset): Port on the syslog server used by the specified protocol.
        transport_protocol (ESyslogServerProtocol | Unset): Transport mode.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the syslog server identity.
    """

    server_name: str
    port: int | Unset = UNSET
    transport_protocol: ESyslogServerProtocol | Unset = UNSET
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        server_name = self.server_name

        port = self.port

        transport_protocol: str | Unset = UNSET
        if not isinstance(self.transport_protocol, Unset):
            transport_protocol = self.transport_protocol.value

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serverName": server_name,
            }
        )
        if port is not UNSET:
            field_dict["port"] = port
        if transport_protocol is not UNSET:
            field_dict["transportProtocol"] = transport_protocol
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        server_name = d.pop("serverName")

        port = d.pop("port", UNSET)

        _transport_protocol = d.pop("transportProtocol", UNSET)
        transport_protocol: ESyslogServerProtocol | Unset
        if isinstance(_transport_protocol, Unset):
            transport_protocol = UNSET
        else:
            transport_protocol = ESyslogServerProtocol(_transport_protocol)

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        general_options_syslog_server_model = cls(
            server_name=server_name,
            port=port,
            transport_protocol=transport_protocol,
            certificate_thumbprint=certificate_thumbprint,
        )

        general_options_syslog_server_model.additional_properties = d
        return general_options_syslog_server_model

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
