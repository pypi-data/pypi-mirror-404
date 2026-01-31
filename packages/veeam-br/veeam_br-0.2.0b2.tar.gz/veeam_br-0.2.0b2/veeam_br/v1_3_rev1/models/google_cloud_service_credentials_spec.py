from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.google_cloud_service_credentials_existing_account_spec import (
        GoogleCloudServiceCredentialsExistingAccountSpec,
    )


T = TypeVar("T", bound="GoogleCloudServiceCredentialsSpec")


@_attrs_define
class GoogleCloudServiceCredentialsSpec:
    """Credentials settings for Google Cloud service account.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        existing_account (GoogleCloudServiceCredentialsExistingAccountSpec): Settings for modifying existing credentials
            for Google Cloud service account.
        description (str | Unset): Description of the cloud credentials record.
    """

    type_: ECloudCredentialsType
    existing_account: GoogleCloudServiceCredentialsExistingAccountSpec
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        existing_account = self.existing_account.to_dict()

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "existingAccount": existing_account,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.google_cloud_service_credentials_existing_account_spec import (
            GoogleCloudServiceCredentialsExistingAccountSpec,
        )

        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        existing_account = GoogleCloudServiceCredentialsExistingAccountSpec.from_dict(d.pop("existingAccount"))

        description = d.pop("description", UNSET)

        google_cloud_service_credentials_spec = cls(
            type_=type_,
            existing_account=existing_account,
            description=description,
        )

        google_cloud_service_credentials_spec.additional_properties = d
        return google_cloud_service_credentials_spec

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
