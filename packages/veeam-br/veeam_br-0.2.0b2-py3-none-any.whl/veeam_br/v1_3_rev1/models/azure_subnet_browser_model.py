from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureSubnetBrowserModel")


@_attrs_define
class AzureSubnetBrowserModel:
    """Microsoft Azure virtual subnet.

    Attributes:
        subnet_id (str | Unset): Virtual subnet ID.
        subnet_name (str | Unset): Virtual subnet name.
    """

    subnet_id: str | Unset = UNSET
    subnet_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subnet_id = self.subnet_id

        subnet_name = self.subnet_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if subnet_id is not UNSET:
            field_dict["subnetId"] = subnet_id
        if subnet_name is not UNSET:
            field_dict["subnetName"] = subnet_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subnet_id = d.pop("subnetId", UNSET)

        subnet_name = d.pop("subnetName", UNSET)

        azure_subnet_browser_model = cls(
            subnet_id=subnet_id,
            subnet_name=subnet_name,
        )

        azure_subnet_browser_model.additional_properties = d
        return azure_subnet_browser_model

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
