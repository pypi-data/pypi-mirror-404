from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GoogleCloudServiceCredentialsExistingAccountSpec")


@_attrs_define
class GoogleCloudServiceCredentialsExistingAccountSpec:
    """Settings for modifying existing credentials for Google Cloud service account.

    Attributes:
        key_file (str): Base64-encoded string of the content of a JSON key file containing a service account key.
    """

    key_file: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key_file = self.key_file

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "keyFile": key_file,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key_file = d.pop("keyFile")

        google_cloud_service_credentials_existing_account_spec = cls(
            key_file=key_file,
        )

        google_cloud_service_credentials_existing_account_spec.additional_properties = d
        return google_cloud_service_credentials_existing_account_spec

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
