from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.azure_virtual_network_browser_model import AzureVirtualNetworkBrowserModel


T = TypeVar("T", bound="AzureResourceGroupBrowserModel")


@_attrs_define
class AzureResourceGroupBrowserModel:
    """
    Attributes:
        resource_group (str): Resource group name.
        virtual_networks (list[AzureVirtualNetworkBrowserModel]): Array of virtual networks available in the resource
            group.
    """

    resource_group: str
    virtual_networks: list[AzureVirtualNetworkBrowserModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_group = self.resource_group

        virtual_networks = []
        for virtual_networks_item_data in self.virtual_networks:
            virtual_networks_item = virtual_networks_item_data.to_dict()
            virtual_networks.append(virtual_networks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resourceGroup": resource_group,
                "virtualNetworks": virtual_networks,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_virtual_network_browser_model import AzureVirtualNetworkBrowserModel

        d = dict(src_dict)
        resource_group = d.pop("resourceGroup")

        virtual_networks = []
        _virtual_networks = d.pop("virtualNetworks")
        for virtual_networks_item_data in _virtual_networks:
            virtual_networks_item = AzureVirtualNetworkBrowserModel.from_dict(virtual_networks_item_data)

            virtual_networks.append(virtual_networks_item)

        azure_resource_group_browser_model = cls(
            resource_group=resource_group,
            virtual_networks=virtual_networks,
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
