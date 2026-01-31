from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="IBMCloudStorageBrowserSpec")


@_attrs_define
class IBMCloudStorageBrowserSpec:
    """IBM Cloud settings.

    Attributes:
        credentials_id (UUID): ID of the object storage account (for browsing either storage or compute infrastructure).
        service_type (ECloudServiceType): Type of cloud service.
        region_id (str): Region of the IBM Cloud object storage.
        service_point (str): Endpoint address and port number of the IBM Cloud object storage.
        gateway_server_id (UUID | Unset): ID of a gateway server you want to use to connect to the object storage.
            Specify this parameter to check the internet connection of the server. As a gateway server, you can use the
            backup server or any Microsoft Windows or Linux server added to your backup infrastructure. By default, the
            backup server ID is used.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    region_id: str
    service_point: str
    gateway_server_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        region_id = self.region_id

        service_point = self.service_point

        gateway_server_id: str | Unset = UNSET
        if not isinstance(self.gateway_server_id, Unset):
            gateway_server_id = str(self.gateway_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "regionId": region_id,
                "servicePoint": service_point,
            }
        )
        if gateway_server_id is not UNSET:
            field_dict["gatewayServerId"] = gateway_server_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        region_id = d.pop("regionId")

        service_point = d.pop("servicePoint")

        _gateway_server_id = d.pop("gatewayServerId", UNSET)
        gateway_server_id: UUID | Unset
        if isinstance(_gateway_server_id, Unset):
            gateway_server_id = UNSET
        else:
            gateway_server_id = UUID(_gateway_server_id)

        ibm_cloud_storage_browser_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            region_id=region_id,
            service_point=service_point,
            gateway_server_id=gateway_server_id,
        )

        ibm_cloud_storage_browser_spec.additional_properties = d
        return ibm_cloud_storage_browser_spec

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
