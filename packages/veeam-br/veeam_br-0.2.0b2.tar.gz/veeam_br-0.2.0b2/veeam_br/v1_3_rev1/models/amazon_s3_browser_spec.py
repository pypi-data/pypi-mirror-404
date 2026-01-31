from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..models.e_cloud_browser_folder_type import ECloudBrowserFolderType
from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_cloud_browser_filters import AmazonS3CloudBrowserFilters


T = TypeVar("T", bound="AmazonS3BrowserSpec")


@_attrs_define
class AmazonS3BrowserSpec:
    """Settings for Amazon S3 storage.

    Attributes:
        credentials_id (UUID): ID of the object storage account (for browsing either storage or compute infrastructure).
        service_type (ECloudServiceType): Type of cloud service.
        region_type (EAmazonRegionType): AWS region type.
        gateway_server_id (UUID | Unset): ID of a gateway server you want to use to connect to the object storage.
            Specify this parameter to check the internet connection of the server. As a gateway server, you can use the
            backup server or any Microsoft Windows or Linux server added to your backup infrastructure. By default, the
            backup server ID is used.
        folder_type (ECloudBrowserFolderType | Unset): Folder type.
        filters (AmazonS3CloudBrowserFilters | Unset): Amazon S3 hierarchy filters. Using the filters reduces not only
            the number of records in the response body but also the response time.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    region_type: EAmazonRegionType
    gateway_server_id: UUID | Unset = UNSET
    folder_type: ECloudBrowserFolderType | Unset = UNSET
    filters: AmazonS3CloudBrowserFilters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        region_type = self.region_type.value

        gateway_server_id: str | Unset = UNSET
        if not isinstance(self.gateway_server_id, Unset):
            gateway_server_id = str(self.gateway_server_id)

        folder_type: str | Unset = UNSET
        if not isinstance(self.folder_type, Unset):
            folder_type = self.folder_type.value

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "regionType": region_type,
            }
        )
        if gateway_server_id is not UNSET:
            field_dict["gatewayServerId"] = gateway_server_id
        if folder_type is not UNSET:
            field_dict["folderType"] = folder_type
        if filters is not UNSET:
            field_dict["filters"] = filters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_cloud_browser_filters import AmazonS3CloudBrowserFilters

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        _gateway_server_id = d.pop("gatewayServerId", UNSET)
        gateway_server_id: UUID | Unset
        if isinstance(_gateway_server_id, Unset):
            gateway_server_id = UNSET
        else:
            gateway_server_id = UUID(_gateway_server_id)

        _folder_type = d.pop("folderType", UNSET)
        folder_type: ECloudBrowserFolderType | Unset
        if isinstance(_folder_type, Unset):
            folder_type = UNSET
        else:
            folder_type = ECloudBrowserFolderType(_folder_type)

        _filters = d.pop("filters", UNSET)
        filters: AmazonS3CloudBrowserFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = AmazonS3CloudBrowserFilters.from_dict(_filters)

        amazon_s3_browser_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            region_type=region_type,
            gateway_server_id=gateway_server_id,
            folder_type=folder_type,
            filters=filters,
        )

        amazon_s3_browser_spec.additional_properties = d
        return amazon_s3_browser_spec

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
