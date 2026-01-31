from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_network_security_group_browser_model import AzureNetworkSecurityGroupBrowserModel
    from ..models.azure_virtual_network_browser_model import AzureVirtualNetworkBrowserModel


T = TypeVar("T", bound="AzureResourceGroupBrowserModel")


@_attrs_define
class AzureResourceGroupBrowserModel:
    """Microsoft Azure resource group.

    Attributes:
        resource_group (str): Resource group name.
        virtual_networks (list[AzureVirtualNetworkBrowserModel]): Array of virtual networks available in the resource
            group.
        network_security_groups (list[AzureNetworkSecurityGroupBrowserModel] | Unset): Array of network security groups
            available in the resource group.
    """

    resource_group: str
    virtual_networks: list[AzureVirtualNetworkBrowserModel]
    network_security_groups: list[AzureNetworkSecurityGroupBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_group = self.resource_group

        virtual_networks = []
        for virtual_networks_item_data in self.virtual_networks:
            virtual_networks_item = virtual_networks_item_data.to_dict()
            virtual_networks.append(virtual_networks_item)

        network_security_groups: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.network_security_groups, Unset):
            network_security_groups = []
            for network_security_groups_item_data in self.network_security_groups:
                network_security_groups_item = network_security_groups_item_data.to_dict()
                network_security_groups.append(network_security_groups_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resourceGroup": resource_group,
                "virtualNetworks": virtual_networks,
            }
        )
        if network_security_groups is not UNSET:
            field_dict["networkSecurityGroups"] = network_security_groups

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_network_security_group_browser_model import AzureNetworkSecurityGroupBrowserModel
        from ..models.azure_virtual_network_browser_model import AzureVirtualNetworkBrowserModel

        d = dict(src_dict)
        resource_group = d.pop("resourceGroup")

        virtual_networks = []
        _virtual_networks = d.pop("virtualNetworks")
        for virtual_networks_item_data in _virtual_networks:
            virtual_networks_item = AzureVirtualNetworkBrowserModel.from_dict(virtual_networks_item_data)

            virtual_networks.append(virtual_networks_item)

        _network_security_groups = d.pop("networkSecurityGroups", UNSET)
        network_security_groups: list[AzureNetworkSecurityGroupBrowserModel] | Unset = UNSET
        if _network_security_groups is not UNSET:
            network_security_groups = []
            for network_security_groups_item_data in _network_security_groups:
                network_security_groups_item = AzureNetworkSecurityGroupBrowserModel.from_dict(
                    network_security_groups_item_data
                )

                network_security_groups.append(network_security_groups_item)

        azure_resource_group_browser_model = cls(
            resource_group=resource_group,
            virtual_networks=virtual_networks,
            network_security_groups=network_security_groups,
        )

        azure_resource_group_browser_model.additional_properties = d
        return azure_resource_group_browser_model

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
