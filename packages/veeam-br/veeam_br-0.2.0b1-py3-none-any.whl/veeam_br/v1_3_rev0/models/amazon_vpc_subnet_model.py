from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonVPCSubnetModel")


@_attrs_define
class AmazonVPCSubnetModel:
    """Amazon VPC subnet.

    Attributes:
        subnet_name (str | Unset): Subnet name.
        subnet_id (str | Unset): Subnet ID.
    """

    subnet_name: str | Unset = UNSET
    subnet_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subnet_name = self.subnet_name

        subnet_id = self.subnet_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if subnet_name is not UNSET:
            field_dict["subnetName"] = subnet_name
        if subnet_id is not UNSET:
            field_dict["subnetId"] = subnet_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subnet_name = d.pop("subnetName", UNSET)

        subnet_id = d.pop("subnetId", UNSET)

        amazon_vpc_subnet_model = cls(
            subnet_name=subnet_name,
            subnet_id=subnet_id,
        )

        amazon_vpc_subnet_model.additional_properties = d
        return amazon_vpc_subnet_model

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
