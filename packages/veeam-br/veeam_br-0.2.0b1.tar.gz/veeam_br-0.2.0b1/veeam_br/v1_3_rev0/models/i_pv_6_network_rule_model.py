from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IPv6NetworkRuleModel")


@_attrs_define
class IPv6NetworkRuleModel:
    """IPv6 network rule.

    Attributes:
        source_i_pv_6_address (str): IP address of the source VM.
        source_subnet_prefix_length (int): Source subnet prefix length.
        target_i_pv_6_address (str): IP address of the replica.
        target_subnet_prefix_length (int): Target subnet prefix length.
        target_default_gateway (str): Defaul gateway address.
        preferred_dns_server (str | Unset): Preferred DNS server address.
        alternate_dns_server (str | Unset): Alternate WINS server address.
    """

    source_i_pv_6_address: str
    source_subnet_prefix_length: int
    target_i_pv_6_address: str
    target_subnet_prefix_length: int
    target_default_gateway: str
    preferred_dns_server: str | Unset = UNSET
    alternate_dns_server: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_i_pv_6_address = self.source_i_pv_6_address

        source_subnet_prefix_length = self.source_subnet_prefix_length

        target_i_pv_6_address = self.target_i_pv_6_address

        target_subnet_prefix_length = self.target_subnet_prefix_length

        target_default_gateway = self.target_default_gateway

        preferred_dns_server = self.preferred_dns_server

        alternate_dns_server = self.alternate_dns_server

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourceIPv6Address": source_i_pv_6_address,
                "sourceSubnetPrefixLength": source_subnet_prefix_length,
                "targetIPv6Address": target_i_pv_6_address,
                "targetSubnetPrefixLength": target_subnet_prefix_length,
                "targetDefaultGateway": target_default_gateway,
            }
        )
        if preferred_dns_server is not UNSET:
            field_dict["preferredDNSServer"] = preferred_dns_server
        if alternate_dns_server is not UNSET:
            field_dict["alternateDNSServer"] = alternate_dns_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_i_pv_6_address = d.pop("sourceIPv6Address")

        source_subnet_prefix_length = d.pop("sourceSubnetPrefixLength")

        target_i_pv_6_address = d.pop("targetIPv6Address")

        target_subnet_prefix_length = d.pop("targetSubnetPrefixLength")

        target_default_gateway = d.pop("targetDefaultGateway")

        preferred_dns_server = d.pop("preferredDNSServer", UNSET)

        alternate_dns_server = d.pop("alternateDNSServer", UNSET)

        i_pv_6_network_rule_model = cls(
            source_i_pv_6_address=source_i_pv_6_address,
            source_subnet_prefix_length=source_subnet_prefix_length,
            target_i_pv_6_address=target_i_pv_6_address,
            target_subnet_prefix_length=target_subnet_prefix_length,
            target_default_gateway=target_default_gateway,
            preferred_dns_server=preferred_dns_server,
            alternate_dns_server=alternate_dns_server,
        )

        i_pv_6_network_rule_model.additional_properties = d
        return i_pv_6_network_rule_model

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
