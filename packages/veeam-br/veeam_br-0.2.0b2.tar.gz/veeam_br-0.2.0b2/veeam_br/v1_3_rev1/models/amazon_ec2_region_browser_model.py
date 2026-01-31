from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_vpc_browser_model import AmazonVPCBrowserModel


T = TypeVar("T", bound="AmazonEC2RegionBrowserModel")


@_attrs_define
class AmazonEC2RegionBrowserModel:
    """AWS region.

    Attributes:
        region_id (str | Unset): ID of a region where the storage is located.
        vpcs (list[AmazonVPCBrowserModel] | Unset): Array of Amazon Virtual Private Cloud (Amazon VPC) networks.
        instance_types (list[str] | Unset): Array of Amazon instance types.
    """

    region_id: str | Unset = UNSET
    vpcs: list[AmazonVPCBrowserModel] | Unset = UNSET
    instance_types: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        region_id = self.region_id

        vpcs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.vpcs, Unset):
            vpcs = []
            for vpcs_item_data in self.vpcs:
                vpcs_item = vpcs_item_data.to_dict()
                vpcs.append(vpcs_item)

        instance_types: list[str] | Unset = UNSET
        if not isinstance(self.instance_types, Unset):
            instance_types = self.instance_types

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if region_id is not UNSET:
            field_dict["regionId"] = region_id
        if vpcs is not UNSET:
            field_dict["vpcs"] = vpcs
        if instance_types is not UNSET:
            field_dict["instanceTypes"] = instance_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_vpc_browser_model import AmazonVPCBrowserModel

        d = dict(src_dict)
        region_id = d.pop("regionId", UNSET)

        _vpcs = d.pop("vpcs", UNSET)
        vpcs: list[AmazonVPCBrowserModel] | Unset = UNSET
        if _vpcs is not UNSET:
            vpcs = []
            for vpcs_item_data in _vpcs:
                vpcs_item = AmazonVPCBrowserModel.from_dict(vpcs_item_data)

                vpcs.append(vpcs_item)

        instance_types = cast(list[str], d.pop("instanceTypes", UNSET))

        amazon_ec2_region_browser_model = cls(
            region_id=region_id,
            vpcs=vpcs,
            instance_types=instance_types,
        )

        amazon_ec2_region_browser_model.additional_properties = d
        return amazon_ec2_region_browser_model

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
