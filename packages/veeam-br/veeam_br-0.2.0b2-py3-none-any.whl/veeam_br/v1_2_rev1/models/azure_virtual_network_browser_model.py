from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureVirtualNetworkBrowserModel")


@_attrs_define
class AzureVirtualNetworkBrowserModel:
    """
    Attributes:
        virtual_network_name (str | Unset): Virtual network name.
        subnets (list[str] | Unset): Array of subnets.
    """

    virtual_network_name: str | Unset = UNSET
    subnets: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        virtual_network_name = self.virtual_network_name

        subnets: list[str] | Unset = UNSET
        if not isinstance(self.subnets, Unset):
            subnets = self.subnets

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if virtual_network_name is not UNSET:
            field_dict["virtualNetworkName"] = virtual_network_name
        if subnets is not UNSET:
            field_dict["subnets"] = subnets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        virtual_network_name = d.pop("virtualNetworkName", UNSET)

        subnets = cast(list[str], d.pop("subnets", UNSET))

        azure_virtual_network_browser_model = cls(
            virtual_network_name=virtual_network_name,
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
