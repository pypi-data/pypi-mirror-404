from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel


T = TypeVar("T", bound="CloudDirectorViHostImportSpec")


@_attrs_define
class CloudDirectorViHostImportSpec:
    """vCenter Server added to VMware Cloud Director.

    Attributes:
        vi_server_name (str): vCenter Server name.
        vi_credentials (CredentialsImportModel): Credentials used for connection.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity. For details on
            how to get the thumbprint, see [Request TLS Certificate or SSH
            Fingerprint](Connection#operation/GetConnectionCertificate).
    """

    vi_server_name: str
    vi_credentials: CredentialsImportModel
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vi_server_name = self.vi_server_name

        vi_credentials = self.vi_credentials.to_dict()

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "viServerName": vi_server_name,
                "viCredentials": vi_credentials,
            }
        )
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel

        d = dict(src_dict)
        vi_server_name = d.pop("viServerName")

        vi_credentials = CredentialsImportModel.from_dict(d.pop("viCredentials"))

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        cloud_director_vi_host_import_spec = cls(
            vi_server_name=vi_server_name,
            vi_credentials=vi_credentials,
            certificate_thumbprint=certificate_thumbprint,
        )

        cloud_director_vi_host_import_spec.additional_properties = d
        return cloud_director_vi_host_import_spec

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
