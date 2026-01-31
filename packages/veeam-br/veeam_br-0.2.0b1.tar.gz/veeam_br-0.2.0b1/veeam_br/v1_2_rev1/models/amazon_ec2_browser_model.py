from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..models.e_cloud_service_type import ECloudServiceType

if TYPE_CHECKING:
    from ..models.amazon_ec2_region_browser_model import AmazonEC2RegionBrowserModel


T = TypeVar("T", bound="AmazonEC2BrowserModel")


@_attrs_define
class AmazonEC2BrowserModel:
    """
    Attributes:
        credentials_id (UUID): ID of the cloud credentials record.
        service_type (ECloudServiceType): Type of cloud service.
        host_id (UUID): ID of a server used to connect to the object storage.
        region_type (EAmazonRegionType): AWS region type.
        regions (list[AmazonEC2RegionBrowserModel]): Array of regions.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    host_id: UUID
    region_type: EAmazonRegionType
    regions: list[AmazonEC2RegionBrowserModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        host_id = str(self.host_id)

        region_type = self.region_type.value

        regions = []
        for regions_item_data in self.regions:
            regions_item = regions_item_data.to_dict()
            regions.append(regions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "hostId": host_id,
                "regionType": region_type,
                "regions": regions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_ec2_region_browser_model import AmazonEC2RegionBrowserModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        host_id = UUID(d.pop("hostId"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        regions = []
        _regions = d.pop("regions")
        for regions_item_data in _regions:
            regions_item = AmazonEC2RegionBrowserModel.from_dict(regions_item_data)

            regions.append(regions_item)

        amazon_ec2_browser_model = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            host_id=host_id,
            region_type=region_type,
            regions=regions,
        )

        amazon_ec2_browser_model.additional_properties = d
        return amazon_ec2_browser_model

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
