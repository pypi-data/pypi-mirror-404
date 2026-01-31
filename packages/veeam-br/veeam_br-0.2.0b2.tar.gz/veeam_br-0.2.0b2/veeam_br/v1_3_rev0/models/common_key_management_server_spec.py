from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_key_management_server_type import EKeyManagementServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.certificate_upload_spec import CertificateUploadSpec


T = TypeVar("T", bound="CommonKeyManagementServerSpec")


@_attrs_define
class CommonKeyManagementServerSpec:
    """General KMS server settings.

    Attributes:
        name (str): Full DNS name or IP address of the KMS server.
        type_ (EKeyManagementServerType): KMS server type.
        port (int): KMIP port on the backup server. You must open the port manually.
        server_certificate (CertificateUploadSpec): Certificate settings (for certificate-based authentication).
        client_certificate (CertificateUploadSpec): Certificate settings (for certificate-based authentication).
        description (str | Unset): KMS server description.
    """

    name: str
    type_: EKeyManagementServerType
    port: int
    server_certificate: CertificateUploadSpec
    client_certificate: CertificateUploadSpec
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        port = self.port

        server_certificate = self.server_certificate.to_dict()

        client_certificate = self.client_certificate.to_dict()

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "port": port,
                "serverCertificate": server_certificate,
                "clientCertificate": client_certificate,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.certificate_upload_spec import CertificateUploadSpec

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EKeyManagementServerType(d.pop("type"))

        port = d.pop("port")

        server_certificate = CertificateUploadSpec.from_dict(d.pop("serverCertificate"))

        client_certificate = CertificateUploadSpec.from_dict(d.pop("clientCertificate"))

        description = d.pop("description", UNSET)

        common_key_management_server_spec = cls(
            name=name,
            type_=type_,
            port=port,
            server_certificate=server_certificate,
            client_certificate=client_certificate,
            description=description,
        )

        common_key_management_server_spec.additional_properties = d
        return common_key_management_server_spec

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
