from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.certificate_upload_spec import CertificateUploadSpec


T = TypeVar("T", bound="AzureComputeCloudCredentialsSubscriptionSpec")


@_attrs_define
class AzureComputeCloudCredentialsSubscriptionSpec:
    """Microsoft Azure compute account. For password-based authentication, specify client secret. For certificate-based
    authentication, specify certificate and password.

        Attributes:
            tenant_id (str): ID of a tenant where the Microsoft Entra ID application is registered in.
            application_id (str): Client ID assigned to the Microsoft Entra ID application.
            secret (str | Unset): (For password-based authentication) Client secret assigned to the Microsoft Entra ID
                application.
            certificate (CertificateUploadSpec | Unset): Certificate settings (for certificate-based authentication).
    """

    tenant_id: str
    application_id: str
    secret: str | Unset = UNSET
    certificate: CertificateUploadSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        application_id = self.application_id

        secret = self.secret

        certificate: dict[str, Any] | Unset = UNSET
        if not isinstance(self.certificate, Unset):
            certificate = self.certificate.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenantId": tenant_id,
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
        tenant_id = d.pop("tenantId")

        application_id = d.pop("applicationId")

        secret = d.pop("secret", UNSET)

        _certificate = d.pop("certificate", UNSET)
        certificate: CertificateUploadSpec | Unset
        if isinstance(_certificate, Unset):
            certificate = UNSET
        else:
            certificate = CertificateUploadSpec.from_dict(_certificate)

        azure_compute_cloud_credentials_subscription_spec = cls(
            tenant_id=tenant_id,
            application_id=application_id,
            secret=secret,
            certificate=certificate,
        )

        azure_compute_cloud_credentials_subscription_spec.additional_properties = d
        return azure_compute_cloud_credentials_subscription_spec

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
