from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ViHostSpec")


@_attrs_define
class ViHostSpec:
    """Settings for VMware vSphere server.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials_id (UUID): ID of the credentials used to connect to the server.
        port (int | Unset): Port used to communicate with the server.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity. For details on
            how to get the thumbprint, see [Request TLS Certificate or SSH
            Fingerprint](Connection#operation/GetConnectionCertificate).
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials_id: UUID
    port: int | Unset = UNSET
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials_id = str(self.credentials_id)

        port = self.port

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "credentialsId": credentials_id,
            }
        )
        if port is not UNSET:
            field_dict["port"] = port
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        credentials_id = UUID(d.pop("credentialsId"))

        port = d.pop("port", UNSET)

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        vi_host_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials_id=credentials_id,
            port=port,
            certificate_thumbprint=certificate_thumbprint,
        )

        vi_host_spec.additional_properties = d
        return vi_host_spec

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
