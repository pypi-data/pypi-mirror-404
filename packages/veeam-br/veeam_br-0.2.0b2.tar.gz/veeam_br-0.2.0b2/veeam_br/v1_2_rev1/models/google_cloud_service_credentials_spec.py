from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..models.e_google_cloud_service_credentials_creation_mode import EGoogleCloudServiceCredentialsCreationMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.google_cloud_service_credentials_existing_account_spec import (
        GoogleCloudServiceCredentialsExistingAccountSpec,
    )


T = TypeVar("T", bound="GoogleCloudServiceCredentialsSpec")


@_attrs_define
class GoogleCloudServiceCredentialsSpec:
    """
    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        creation_mode (EGoogleCloudServiceCredentialsCreationMode): Mode that defines whether you want to create a new
            Google Cloud service account or connect an existing one.
        description (str | Unset): Description of the cloud credentials record.
        existing_account (GoogleCloudServiceCredentialsExistingAccountSpec | Unset):
    """

    type_: ECloudCredentialsType
    creation_mode: EGoogleCloudServiceCredentialsCreationMode
    description: str | Unset = UNSET
    existing_account: GoogleCloudServiceCredentialsExistingAccountSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        creation_mode = self.creation_mode.value

        description = self.description

        existing_account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.existing_account, Unset):
            existing_account = self.existing_account.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "creationMode": creation_mode,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if existing_account is not UNSET:
            field_dict["existingAccount"] = existing_account

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.google_cloud_service_credentials_existing_account_spec import (
            GoogleCloudServiceCredentialsExistingAccountSpec,
        )

        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        creation_mode = EGoogleCloudServiceCredentialsCreationMode(d.pop("creationMode"))

        description = d.pop("description", UNSET)

        _existing_account = d.pop("existingAccount", UNSET)
        existing_account: GoogleCloudServiceCredentialsExistingAccountSpec | Unset
        if isinstance(_existing_account, Unset):
            existing_account = UNSET
        else:
            existing_account = GoogleCloudServiceCredentialsExistingAccountSpec.from_dict(_existing_account)

        google_cloud_service_credentials_spec = cls(
            type_=type_,
            creation_mode=creation_mode,
            description=description,
            existing_account=existing_account,
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
