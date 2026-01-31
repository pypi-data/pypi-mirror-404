from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonSnowballEdgeBrowserDestinationSpec")


@_attrs_define
class AmazonSnowballEdgeBrowserDestinationSpec:
    """Settings for creating a new folder in AWS Snowball Edge storage.

    Attributes:
        credentials_id (UUID): ID of a cloud credentials record required to connect to the object storage.
        service_type (ECloudServiceType): Type of cloud service.
        new_folder_name (str): Name of the new folder.
        connection_point (str): Service point address and port number of the AWS Snowball Edge device.
        region_id (str): For AWS Snowball Edge, the region is *snow*.
        bucket_name (str): Name of the bucket where you want to store your backup data.
        host_id (UUID | Unset): ID of a server you want to use to connect to the object storage. You can use the backup
            server or any Microsoft Windows or Linux server added to your backup infrastructure. By default, the backup
            server ID is used.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    new_folder_name: str
    connection_point: str
    region_id: str
    bucket_name: str
    host_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        new_folder_name = self.new_folder_name

        connection_point = self.connection_point

        region_id = self.region_id

        bucket_name = self.bucket_name

        host_id: str | Unset = UNSET
        if not isinstance(self.host_id, Unset):
            host_id = str(self.host_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "newFolderName": new_folder_name,
                "connectionPoint": connection_point,
                "regionId": region_id,
                "bucketName": bucket_name,
            }
        )
        if host_id is not UNSET:
            field_dict["hostId"] = host_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        new_folder_name = d.pop("newFolderName")

        connection_point = d.pop("connectionPoint")

        region_id = d.pop("regionId")

        bucket_name = d.pop("bucketName")

        _host_id = d.pop("hostId", UNSET)
        host_id: UUID | Unset
        if isinstance(_host_id, Unset):
            host_id = UNSET
        else:
            host_id = UUID(_host_id)

        amazon_snowball_edge_browser_destination_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            new_folder_name=new_folder_name,
            connection_point=connection_point,
            region_id=region_id,
            bucket_name=bucket_name,
            host_id=host_id,
        )

        amazon_snowball_edge_browser_destination_spec.additional_properties = d
        return amazon_snowball_edge_browser_destination_spec

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
