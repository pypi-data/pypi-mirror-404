from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="CertificateModel")


@_attrs_define
class CertificateModel:
    """Certificate settings.

    Attributes:
        thumbprint (str): Thumbprint of the certificate.
        serial_number (str): Serial number of the certificate.
        key_algorithm (str): Key algorithm of the certificate.
        key_size (str): Key size of the certificate.
        subject (str): Subject of the certificate.
        issued_to (str): Acquirer of the certificate.
        issued_by (str): Issuer of the certificate.
        valid_from (datetime.datetime): Date and time the certificate is valid from.
        valid_by (datetime.datetime): Expiration date and time of the certificate.
    """

    thumbprint: str
    serial_number: str
    key_algorithm: str
    key_size: str
    subject: str
    issued_to: str
    issued_by: str
    valid_from: datetime.datetime
    valid_by: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        thumbprint = self.thumbprint

        serial_number = self.serial_number

        key_algorithm = self.key_algorithm

        key_size = self.key_size

        subject = self.subject

        issued_to = self.issued_to

        issued_by = self.issued_by

        valid_from = self.valid_from.isoformat()

        valid_by = self.valid_by.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "thumbprint": thumbprint,
                "serialNumber": serial_number,
                "keyAlgorithm": key_algorithm,
                "keySize": key_size,
                "subject": subject,
                "issuedTo": issued_to,
                "issuedBy": issued_by,
                "validFrom": valid_from,
                "validBy": valid_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        thumbprint = d.pop("thumbprint")

        serial_number = d.pop("serialNumber")

        key_algorithm = d.pop("keyAlgorithm")

        key_size = d.pop("keySize")

        subject = d.pop("subject")

        issued_to = d.pop("issuedTo")

        issued_by = d.pop("issuedBy")

        valid_from = isoparse(d.pop("validFrom"))

        valid_by = isoparse(d.pop("validBy"))

        certificate_model = cls(
            thumbprint=thumbprint,
            serial_number=serial_number,
            key_algorithm=key_algorithm,
            key_size=key_size,
            subject=subject,
            issued_to=issued_to,
            issued_by=issued_by,
            valid_from=valid_from,
            valid_by=valid_by,
        )

        certificate_model.additional_properties = d
        return certificate_model

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
