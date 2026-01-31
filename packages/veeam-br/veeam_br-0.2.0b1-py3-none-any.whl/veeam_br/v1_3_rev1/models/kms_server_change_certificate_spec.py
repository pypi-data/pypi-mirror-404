from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ekms_certificate_type import EKMSCertificateType

if TYPE_CHECKING:
    from ..models.certificate_upload_spec import CertificateUploadSpec


T = TypeVar("T", bound="KMSServerChangeCertificateSpec")


@_attrs_define
class KMSServerChangeCertificateSpec:
    """Settings for changing the certificate of a KMS server.

    Attributes:
        certificate (CertificateUploadSpec): Certificate settings (for certificate-based authentication).
        type_ (EKMSCertificateType): Certificate type.
    """

    certificate: CertificateUploadSpec
    type_: EKMSCertificateType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        certificate = self.certificate.to_dict()

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "certificate": certificate,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.certificate_upload_spec import CertificateUploadSpec

        d = dict(src_dict)
        certificate = CertificateUploadSpec.from_dict(d.pop("certificate"))

        type_ = EKMSCertificateType(d.pop("type"))

        kms_server_change_certificate_spec = cls(
            certificate=certificate,
            type_=type_,
        )

        kms_server_change_certificate_spec.additional_properties = d
        return kms_server_change_certificate_spec

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
