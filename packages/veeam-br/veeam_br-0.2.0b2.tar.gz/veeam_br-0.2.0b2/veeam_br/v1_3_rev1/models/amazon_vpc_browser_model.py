from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_vpc_subnet_model import AmazonVPCSubnetModel


T = TypeVar("T", bound="AmazonVPCBrowserModel")


@_attrs_define
class AmazonVPCBrowserModel:
    """Amazon VPC.

    Attributes:
        vpc_name (str | Unset): VPC name.
        vpc_id (str | Unset): VPC ID.
        subnets (list[AmazonVPCSubnetModel] | Unset): Array of VPC subnets.
        security_groups (list[str] | Unset): Array of security groups.
    """

    vpc_name: str | Unset = UNSET
    vpc_id: str | Unset = UNSET
    subnets: list[AmazonVPCSubnetModel] | Unset = UNSET
    security_groups: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vpc_name = self.vpc_name

        vpc_id = self.vpc_id

        subnets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.subnets, Unset):
            subnets = []
            for subnets_item_data in self.subnets:
                subnets_item = subnets_item_data.to_dict()
                subnets.append(subnets_item)

        security_groups: list[str] | Unset = UNSET
        if not isinstance(self.security_groups, Unset):
            security_groups = self.security_groups

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vpc_name is not UNSET:
            field_dict["vpcName"] = vpc_name
        if vpc_id is not UNSET:
            field_dict["vpcId"] = vpc_id
        if subnets is not UNSET:
            field_dict["subnets"] = subnets
        if security_groups is not UNSET:
            field_dict["securityGroups"] = security_groups

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_vpc_subnet_model import AmazonVPCSubnetModel

        d = dict(src_dict)
        vpc_name = d.pop("vpcName", UNSET)

        vpc_id = d.pop("vpcId", UNSET)

        _subnets = d.pop("subnets", UNSET)
        subnets: list[AmazonVPCSubnetModel] | Unset = UNSET
        if _subnets is not UNSET:
            subnets = []
            for subnets_item_data in _subnets:
                subnets_item = AmazonVPCSubnetModel.from_dict(subnets_item_data)

                subnets.append(subnets_item)

        security_groups = cast(list[str], d.pop("securityGroups", UNSET))

        amazon_vpc_browser_model = cls(
            vpc_name=vpc_name,
            vpc_id=vpc_id,
            subnets=subnets,
            security_groups=security_groups,
        )

        amazon_vpc_browser_model.additional_properties = d
        return amazon_vpc_browser_model

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
