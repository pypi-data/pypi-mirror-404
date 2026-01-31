from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType

T = TypeVar("T", bound="SpecifiedGuestOsCredentialsModel")


@_attrs_define
class SpecifiedGuestOsCredentialsModel:
    """Custom credentials.

    Attributes:
        credentials_id (UUID): Credentials ID for Microsoft Windows machines.
        credentials_type (ECredentialsType): Credentials type.
    """

    credentials_id: UUID
    credentials_type: ECredentialsType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        credentials_type = self.credentials_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "credentialsType": credentials_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        credentials_type = ECredentialsType(d.pop("credentialsType"))

        specified_guest_os_credentials_model = cls(
            credentials_id=credentials_id,
            credentials_type=credentials_type,
        )

        specified_guest_os_credentials_model.additional_properties = d
        return specified_guest_os_credentials_model

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
