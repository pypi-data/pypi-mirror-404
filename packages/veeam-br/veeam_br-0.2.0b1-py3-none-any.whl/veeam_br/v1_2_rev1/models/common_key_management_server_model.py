from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_key_management_server_type import EKeyManagementServerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CommonKeyManagementServerModel")


@_attrs_define
class CommonKeyManagementServerModel:
    """
    Attributes:
        id (UUID): ID of the KMS server.
        name (str): Full DNS name or IP address of the KMS server.
        type_ (EKeyManagementServerType): KMS server type.
        port (int): KMIP port on the backup server.
        description (str | Unset): KMS server description.
        server_certificate_thumbprint (str | Unset): Thumbprint of the KMS server certificate.
        client_certificate_thumbprint (str | Unset): Thumbprint of the client certificate created on the KMS server.
    """

    id: UUID
    name: str
    type_: EKeyManagementServerType
    port: int
    description: str | Unset = UNSET
    server_certificate_thumbprint: str | Unset = UNSET
    client_certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        port = self.port

        description = self.description

        server_certificate_thumbprint = self.server_certificate_thumbprint

        client_certificate_thumbprint = self.client_certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "port": port,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if server_certificate_thumbprint is not UNSET:
            field_dict["serverCertificateThumbprint"] = server_certificate_thumbprint
        if client_certificate_thumbprint is not UNSET:
            field_dict["clientCertificateThumbprint"] = client_certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EKeyManagementServerType(d.pop("type"))

        port = d.pop("port")

        description = d.pop("description", UNSET)

        server_certificate_thumbprint = d.pop("serverCertificateThumbprint", UNSET)

        client_certificate_thumbprint = d.pop("clientCertificateThumbprint", UNSET)

        common_key_management_server_model = cls(
            id=id,
            name=name,
            type_=type_,
            port=port,
            description=description,
            server_certificate_thumbprint=server_certificate_thumbprint,
            client_certificate_thumbprint=client_certificate_thumbprint,
        )

        common_key_management_server_model.additional_properties = d
        return common_key_management_server_model

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
