from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_vi_host_model import CloudDirectorViHostModel


T = TypeVar("T", bound="CloudDirectorHostModel")


@_attrs_define
class CloudDirectorHostModel:
    """VMware Cloud Director server.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_id (UUID): ID of the credentials used to connect to the server.
        vi_servers (list[CloudDirectorViHostModel]): Array of vCenter Servers added to VMware Cloud Director.
        url (str | Unset): URL of the VMware Cloud Director server.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_id: UUID
    vi_servers: list[CloudDirectorViHostModel]
    url: str | Unset = UNSET
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_id = str(self.credentials_id)

        vi_servers = []
        for vi_servers_item_data in self.vi_servers:
            vi_servers_item = vi_servers_item_data.to_dict()
            vi_servers.append(vi_servers_item)

        url = self.url

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
                "credentialsId": credentials_id,
                "viServers": vi_servers,
            }
        )
        if url is not UNSET:
            field_dict["url"] = url
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_vi_host_model import CloudDirectorViHostModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_id = UUID(d.pop("credentialsId"))

        vi_servers = []
        _vi_servers = d.pop("viServers")
        for vi_servers_item_data in _vi_servers:
            vi_servers_item = CloudDirectorViHostModel.from_dict(vi_servers_item_data)

            vi_servers.append(vi_servers_item)

        url = d.pop("url", UNSET)

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        cloud_director_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_id=credentials_id,
            vi_servers=vi_servers,
            url=url,
            certificate_thumbprint=certificate_thumbprint,
        )

        cloud_director_host_model.additional_properties = d
        return cloud_director_host_model

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
