from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeNetworkModel")


@_attrs_define
class AzureComputeNetworkModel:
    """Microsoft Azure VM network settings.

    Attributes:
        network (str): Microsoft Azure virtual network.
        subnet (str): Microsoft Azure virtual subnet for the production VM. Make sure that the production VM subnet is
            different than the one you specify for the Instant Recovery helper appliance.
        network_security_group (str | Unset): Security group for the recovered workload.
        assign_public_ip (bool | Unset): If `true`, a public IP will be assigned to the restored VM.
    """

    network: str
    subnet: str
    network_security_group: str | Unset = UNSET
    assign_public_ip: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        network = self.network

        subnet = self.subnet

        network_security_group = self.network_security_group

        assign_public_ip = self.assign_public_ip

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "network": network,
                "subnet": subnet,
            }
        )
        if network_security_group is not UNSET:
            field_dict["networkSecurityGroup"] = network_security_group
        if assign_public_ip is not UNSET:
            field_dict["assignPublicIp"] = assign_public_ip

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        network = d.pop("network")

        subnet = d.pop("subnet")

        network_security_group = d.pop("networkSecurityGroup", UNSET)

        assign_public_ip = d.pop("assignPublicIp", UNSET)

        azure_compute_network_model = cls(
            network=network,
            subnet=subnet,
            network_security_group=network_security_group,
            assign_public_ip=assign_public_ip,
        )

        azure_compute_network_model.additional_properties = d
        return azure_compute_network_model

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
