from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ad_object_custom_credentials_model import ADObjectCustomCredentialsModel


T = TypeVar("T", bound="ADObjectsProtectionGroupCredentialModel")


@_attrs_define
class ADObjectsProtectionGroupCredentialModel:
    """Authentication settings for Active Directory objects.

    Attributes:
        master_credentials_id (UUID): Master account credentials for authenticating with all Active Directory objects in
            a protection scope.
        use_custom_credentials (bool): If `true`, custom credentials are used for authenticating with the specified
            Active Directory objects.
        custom_credentials (list[ADObjectCustomCredentialsModel] | Unset): Array of credentials for authenticating to
            the specified Active Directory objects.
    """

    master_credentials_id: UUID
    use_custom_credentials: bool
    custom_credentials: list[ADObjectCustomCredentialsModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        master_credentials_id = str(self.master_credentials_id)

        use_custom_credentials = self.use_custom_credentials

        custom_credentials: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.custom_credentials, Unset):
            custom_credentials = []
            for custom_credentials_item_data in self.custom_credentials:
                custom_credentials_item = custom_credentials_item_data.to_dict()
                custom_credentials.append(custom_credentials_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "masterCredentialsId": master_credentials_id,
                "useCustomCredentials": use_custom_credentials,
            }
        )
        if custom_credentials is not UNSET:
            field_dict["customCredentials"] = custom_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ad_object_custom_credentials_model import ADObjectCustomCredentialsModel

        d = dict(src_dict)
        master_credentials_id = UUID(d.pop("masterCredentialsId"))

        use_custom_credentials = d.pop("useCustomCredentials")

        _custom_credentials = d.pop("customCredentials", UNSET)
        custom_credentials: list[ADObjectCustomCredentialsModel] | Unset = UNSET
        if _custom_credentials is not UNSET:
            custom_credentials = []
            for custom_credentials_item_data in _custom_credentials:
                custom_credentials_item = ADObjectCustomCredentialsModel.from_dict(custom_credentials_item_data)

                custom_credentials.append(custom_credentials_item)

        ad_objects_protection_group_credential_model = cls(
            master_credentials_id=master_credentials_id,
            use_custom_credentials=use_custom_credentials,
            custom_credentials=custom_credentials,
        )

        ad_objects_protection_group_credential_model.additional_properties = d
        return ad_objects_protection_group_credential_model

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
