from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IPv6SettingsModel")


@_attrs_define
class IPv6SettingsModel:
    """IPv6 settings.

    Attributes:
        ip_address (str): Helper appliance IP address.
        prefix_length (int | Unset): Subnet prefix length.
        default_gateway (str | Unset): Default gateway address.
        preferred_dns_server (str | Unset): Preferred DNS server address.
        alternate_dns_server (str | Unset): Alternate DNS server address.
    """

    ip_address: str
    prefix_length: int | Unset = UNSET
    default_gateway: str | Unset = UNSET
    preferred_dns_server: str | Unset = UNSET
    alternate_dns_server: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip_address = self.ip_address

        prefix_length = self.prefix_length

        default_gateway = self.default_gateway

        preferred_dns_server = self.preferred_dns_server

        alternate_dns_server = self.alternate_dns_server

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ipAddress": ip_address,
            }
        )
        if prefix_length is not UNSET:
            field_dict["prefixLength"] = prefix_length
        if default_gateway is not UNSET:
            field_dict["defaultGateway"] = default_gateway
        if preferred_dns_server is not UNSET:
            field_dict["preferredDNSServer"] = preferred_dns_server
        if alternate_dns_server is not UNSET:
            field_dict["alternateDNSServer"] = alternate_dns_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ip_address = d.pop("ipAddress")

        prefix_length = d.pop("prefixLength", UNSET)

        default_gateway = d.pop("defaultGateway", UNSET)

        preferred_dns_server = d.pop("preferredDNSServer", UNSET)

        alternate_dns_server = d.pop("alternateDNSServer", UNSET)

        i_pv_6_settings_model = cls(
            ip_address=ip_address,
            prefix_length=prefix_length,
            default_gateway=default_gateway,
            preferred_dns_server=preferred_dns_server,
            alternate_dns_server=alternate_dns_server,
        )

        i_pv_6_settings_model.additional_properties = d
        return i_pv_6_settings_model

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
