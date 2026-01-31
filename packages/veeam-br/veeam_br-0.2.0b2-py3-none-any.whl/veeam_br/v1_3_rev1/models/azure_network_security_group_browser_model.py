from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureNetworkSecurityGroupBrowserModel")


@_attrs_define
class AzureNetworkSecurityGroupBrowserModel:
    """Microsoft Azure security group.

    Attributes:
        network_security_id (str | Unset): Security group ID.
        network_security_name (str | Unset): Security group name.
    """

    network_security_id: str | Unset = UNSET
    network_security_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        network_security_id = self.network_security_id

        network_security_name = self.network_security_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if network_security_id is not UNSET:
            field_dict["networkSecurityId"] = network_security_id
        if network_security_name is not UNSET:
            field_dict["networkSecurityName"] = network_security_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        network_security_id = d.pop("networkSecurityId", UNSET)

        network_security_name = d.pop("networkSecurityName", UNSET)

        azure_network_security_group_browser_model = cls(
            network_security_id=network_security_id,
            network_security_name=network_security_name,
        )

        azure_network_security_group_browser_model.additional_properties = d
        return azure_network_security_group_browser_model

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
