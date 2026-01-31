from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_certificate_file_format_type import ECertificateFileFormatType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CertificateUploadSpec")


@_attrs_define
class CertificateUploadSpec:
    """Certificate settings (for certificate-based authentication).

    Attributes:
        certificate (str): Base64-encoded string of the content of a PFX certificate file.
        format_type (ECertificateFileFormatType): Certificate file format.
        password (str | Unset): Decryption password for the certificate file.
    """

    certificate: str
    format_type: ECertificateFileFormatType
    password: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        certificate = self.certificate

        format_type = self.format_type.value

        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "certificate": certificate,
                "formatType": format_type,
            }
        )
        if password is not UNSET:
            field_dict["password"] = password

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        certificate = d.pop("certificate")

        format_type = ECertificateFileFormatType(d.pop("formatType"))

        password = d.pop("password", UNSET)

        certificate_upload_spec = cls(
            certificate=certificate,
            format_type=format_type,
            password=password,
        )

        certificate_upload_spec.additional_properties = d
        return certificate_upload_spec

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
