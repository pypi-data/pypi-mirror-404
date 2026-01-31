from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PreferredNetworkModel")


@_attrs_define
class PreferredNetworkModel:
    """Preferred network used for Veeam Backup & Replication traffic.

    Attributes:
        ip_address (str | Unset): IP address.
        subnet_mask (str | Unset): Subnet mask.
        cidr_notation (str | Unset): CIDR notation.
    """

    ip_address: str | Unset = UNSET
    subnet_mask: str | Unset = UNSET
    cidr_notation: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip_address = self.ip_address

        subnet_mask = self.subnet_mask

        cidr_notation = self.cidr_notation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ip_address is not UNSET:
            field_dict["ipAddress"] = ip_address
        if subnet_mask is not UNSET:
            field_dict["subnetMask"] = subnet_mask
        if cidr_notation is not UNSET:
            field_dict["cidrNotation"] = cidr_notation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ip_address = d.pop("ipAddress", UNSET)

        subnet_mask = d.pop("subnetMask", UNSET)

        cidr_notation = d.pop("cidrNotation", UNSET)

        preferred_network_model = cls(
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            cidr_notation=cidr_notation,
        )

        preferred_network_model.additional_properties = d
        return preferred_network_model

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
