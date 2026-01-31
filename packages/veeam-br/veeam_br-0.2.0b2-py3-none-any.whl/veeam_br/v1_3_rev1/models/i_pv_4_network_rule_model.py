from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IPv4NetworkRuleModel")


@_attrs_define
class IPv4NetworkRuleModel:
    """IPv4 network rule.

    Attributes:
        source_ip_address (str): IP address of the source VM.
        source_subnet_mask (str): Subnet mask of the source VM.
        target_ip_address (str): IP address of the replica.
        target_subnet_mask (str): Subnet mask of the replica.
        target_default_gateway (str): Default gateway address.
        preferred_dns_server (str | Unset): Preferred DNS server address.
        alternate_dns_server (str | Unset): Alternate DNS server address.
        preferred_wins_server (str | Unset): Preferred WINS server address.
        alternate_wins_server (str | Unset): Alternate WINS server address.
    """

    source_ip_address: str
    source_subnet_mask: str
    target_ip_address: str
    target_subnet_mask: str
    target_default_gateway: str
    preferred_dns_server: str | Unset = UNSET
    alternate_dns_server: str | Unset = UNSET
    preferred_wins_server: str | Unset = UNSET
    alternate_wins_server: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_ip_address = self.source_ip_address

        source_subnet_mask = self.source_subnet_mask

        target_ip_address = self.target_ip_address

        target_subnet_mask = self.target_subnet_mask

        target_default_gateway = self.target_default_gateway

        preferred_dns_server = self.preferred_dns_server

        alternate_dns_server = self.alternate_dns_server

        preferred_wins_server = self.preferred_wins_server

        alternate_wins_server = self.alternate_wins_server

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourceIPAddress": source_ip_address,
                "sourceSubnetMask": source_subnet_mask,
                "targetIPAddress": target_ip_address,
                "targetSubnetMask": target_subnet_mask,
                "targetDefaultGateway": target_default_gateway,
            }
        )
        if preferred_dns_server is not UNSET:
            field_dict["preferredDNSServer"] = preferred_dns_server
        if alternate_dns_server is not UNSET:
            field_dict["alternateDNSServer"] = alternate_dns_server
        if preferred_wins_server is not UNSET:
            field_dict["preferredWINSServer"] = preferred_wins_server
        if alternate_wins_server is not UNSET:
            field_dict["alternateWINSServer"] = alternate_wins_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_ip_address = d.pop("sourceIPAddress")

        source_subnet_mask = d.pop("sourceSubnetMask")

        target_ip_address = d.pop("targetIPAddress")

        target_subnet_mask = d.pop("targetSubnetMask")

        target_default_gateway = d.pop("targetDefaultGateway")

        preferred_dns_server = d.pop("preferredDNSServer", UNSET)

        alternate_dns_server = d.pop("alternateDNSServer", UNSET)

        preferred_wins_server = d.pop("preferredWINSServer", UNSET)

        alternate_wins_server = d.pop("alternateWINSServer", UNSET)

        i_pv_4_network_rule_model = cls(
            source_ip_address=source_ip_address,
            source_subnet_mask=source_subnet_mask,
            target_ip_address=target_ip_address,
            target_subnet_mask=target_subnet_mask,
            target_default_gateway=target_default_gateway,
            preferred_dns_server=preferred_dns_server,
            alternate_dns_server=alternate_dns_server,
            preferred_wins_server=preferred_wins_server,
            alternate_wins_server=alternate_wins_server,
        )

        i_pv_4_network_rule_model.additional_properties = d
        return i_pv_4_network_rule_model

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
