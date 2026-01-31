from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_cloud_credentials_type import ECloudCredentialsType

T = TypeVar("T", bound="AzureComputeCloudDeviceCodeModel")


@_attrs_define
class AzureComputeCloudDeviceCodeModel:
    """Verification code required to register a new Microsoft Entra ID application.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        url (str): Verification URI.
        verification_code (str): Verification code.
        expiration_time (datetime.datetime): Expiration date and time of the verification code. By default, the code is
            valid for 15 minutes.
    """

    type_: ECloudCredentialsType
    url: str
    verification_code: str
    expiration_time: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        url = self.url

        verification_code = self.verification_code

        expiration_time = self.expiration_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "url": url,
                "verificationCode": verification_code,
                "expirationTime": expiration_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        url = d.pop("url")

        verification_code = d.pop("verificationCode")

        expiration_time = isoparse(d.pop("expirationTime"))

        azure_compute_cloud_device_code_model = cls(
            type_=type_,
            url=url,
            verification_code=verification_code,
            expiration_time=expiration_time,
        )

        azure_compute_cloud_device_code_model.additional_properties = d
        return azure_compute_cloud_device_code_model

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
