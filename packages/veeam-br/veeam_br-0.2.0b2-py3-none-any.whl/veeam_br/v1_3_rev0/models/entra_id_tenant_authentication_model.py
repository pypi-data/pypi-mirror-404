from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.certificate_upload_spec import CertificateUploadSpec


T = TypeVar("T", bound="EntraIDTenantAuthenticationModel")


@_attrs_define
class EntraIDTenantAuthenticationModel:
    """Authentication settings.

    Attributes:
        application_id (str): Application ID.
        secret (str | Unset): Application (client) secret.
        certificate (CertificateUploadSpec | Unset): Certificate settings (for certificate-based authentication).
    """

    application_id: str
    secret: str | Unset = UNSET
    certificate: CertificateUploadSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        application_id = self.application_id

        secret = self.secret

        certificate: dict[str, Any] | Unset = UNSET
        if not isinstance(self.certificate, Unset):
            certificate = self.certificate.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "applicationId": application_id,
            }
        )
        if secret is not UNSET:
            field_dict["secret"] = secret
        if certificate is not UNSET:
            field_dict["certificate"] = certificate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.certificate_upload_spec import CertificateUploadSpec

        d = dict(src_dict)
        application_id = d.pop("applicationId")

        secret = d.pop("secret", UNSET)

        _certificate = d.pop("certificate", UNSET)
        certificate: CertificateUploadSpec | Unset
        if isinstance(_certificate, Unset):
            certificate = UNSET
        else:
            certificate = CertificateUploadSpec.from_dict(_certificate)

        entra_id_tenant_authentication_model = cls(
            application_id=application_id,
            secret=secret,
            certificate=certificate,
        )

        entra_id_tenant_authentication_model.additional_properties = d
        return entra_id_tenant_authentication_model

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
