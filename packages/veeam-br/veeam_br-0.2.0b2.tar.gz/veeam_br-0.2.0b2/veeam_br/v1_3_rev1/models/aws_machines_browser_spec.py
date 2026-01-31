from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aws_machines_browser_filters import AWSMachinesBrowserFilters


T = TypeVar("T", bound="AWSMachinesBrowserSpec")


@_attrs_define
class AWSMachinesBrowserSpec:
    """Amazon EC2 settings.

    Attributes:
        service_type (EProtectionGroupCloudAccountType): Cloud account type.
        credentials_id (UUID): ID of the object storage account (for browsing either storage or EC2 infrastructure).
        region_type (EAmazonRegionType): AWS region type.
        region (str): Filters EC2 resources by Amazon region name.
        filters (AWSMachinesBrowserFilters | Unset): Amazon machines filters. Using the filters reduces not only the
            number of records in the response body but also the response time.
    """

    service_type: EProtectionGroupCloudAccountType
    credentials_id: UUID
    region_type: EAmazonRegionType
    region: str
    filters: AWSMachinesBrowserFilters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_type = self.service_type.value

        credentials_id = str(self.credentials_id)

        region_type = self.region_type.value

        region = self.region

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serviceType": service_type,
                "credentialsId": credentials_id,
                "regionType": region_type,
                "region": region,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_machines_browser_filters import AWSMachinesBrowserFilters

        d = dict(src_dict)
        service_type = EProtectionGroupCloudAccountType(d.pop("serviceType"))

        credentials_id = UUID(d.pop("credentialsId"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        region = d.pop("region")

        _filters = d.pop("filters", UNSET)
        filters: AWSMachinesBrowserFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = AWSMachinesBrowserFilters.from_dict(_filters)

        aws_machines_browser_spec = cls(
            service_type=service_type,
            credentials_id=credentials_id,
            region_type=region_type,
            region=region,
            filters=filters,
        )

        aws_machines_browser_spec.additional_properties = d
        return aws_machines_browser_spec

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
