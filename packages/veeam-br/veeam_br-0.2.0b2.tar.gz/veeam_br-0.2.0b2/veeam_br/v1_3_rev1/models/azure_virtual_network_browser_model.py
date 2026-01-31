from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_subnet_browser_model import AzureSubnetBrowserModel


T = TypeVar("T", bound="AzureVirtualNetworkBrowserModel")


@_attrs_define
class AzureVirtualNetworkBrowserModel:
    """Microsoft Azure virtual network.

    Attributes:
        virtual_network_name (str | Unset): Virtual network name.
        virtual_network_id (str | Unset): Virtual network ID.
        subnets (list[AzureSubnetBrowserModel] | Unset): Array of subnets.
    """

    virtual_network_name: str | Unset = UNSET
    virtual_network_id: str | Unset = UNSET
    subnets: list[AzureSubnetBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        virtual_network_name = self.virtual_network_name

        virtual_network_id = self.virtual_network_id

        subnets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.subnets, Unset):
            subnets = []
            for subnets_item_data in self.subnets:
                subnets_item = subnets_item_data.to_dict()
                subnets.append(subnets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if virtual_network_name is not UNSET:
            field_dict["virtualNetworkName"] = virtual_network_name
        if virtual_network_id is not UNSET:
            field_dict["virtualNetworkId"] = virtual_network_id
        if subnets is not UNSET:
            field_dict["subnets"] = subnets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_subnet_browser_model import AzureSubnetBrowserModel

        d = dict(src_dict)
        virtual_network_name = d.pop("virtualNetworkName", UNSET)

        virtual_network_id = d.pop("virtualNetworkId", UNSET)

        _subnets = d.pop("subnets", UNSET)
        subnets: list[AzureSubnetBrowserModel] | Unset = UNSET
        if _subnets is not UNSET:
            subnets = []
            for subnets_item_data in _subnets:
                subnets_item = AzureSubnetBrowserModel.from_dict(subnets_item_data)

                subnets.append(subnets_item)

        azure_virtual_network_browser_model = cls(
            virtual_network_name=virtual_network_name,
            virtual_network_id=virtual_network_id,
            subnets=subnets,
        )

        azure_virtual_network_browser_model.additional_properties = d
        return azure_virtual_network_browser_model

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
