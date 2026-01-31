from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudDirectorHostDiscoverySpec")


@_attrs_define
class CloudDirectorHostDiscoverySpec:
    """Settings for discovery of VMware Cloud Director server.

    Attributes:
        url (str): URL of the VMware Cloud Director server.
        credentials_id (UUID): ID of the credentials used to connect to the server.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity. For details on
            how to get the thumbprint, see [Request TLS Certificate or SSH
            Fingerprint](Connection#operation/GetConnectionCertificate).
    """

    url: str
    credentials_id: UUID
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        credentials_id = str(self.credentials_id)

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "url": url,
                "credentialsId": credentials_id,
            }
        )
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        credentials_id = UUID(d.pop("credentialsId"))

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        cloud_director_host_discovery_spec = cls(
            url=url,
            credentials_id=credentials_id,
            certificate_thumbprint=certificate_thumbprint,
        )

        cloud_director_host_discovery_spec.additional_properties = d
        return cloud_director_host_discovery_spec

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
