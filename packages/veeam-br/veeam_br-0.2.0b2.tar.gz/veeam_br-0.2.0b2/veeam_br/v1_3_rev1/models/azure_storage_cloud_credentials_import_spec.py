from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureStorageCloudCredentialsImportSpec")


@_attrs_define
class AzureStorageCloudCredentialsImportSpec:
    """Settings for importing Microsoft Azure storage cloud credentials.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        unique_id (str): Unique ID that identifies the cloud credentials record.
        account (str): Name of the Microsoft Azure storage account.
        shared_key (str): Shared key of the Microsoft Azure storage account.
        description (str | Unset): Description of the cloud credentials record.
    """

    type_: ECloudCredentialsType
    unique_id: str
    account: str
    shared_key: str
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        unique_id = self.unique_id

        account = self.account

        shared_key = self.shared_key

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "uniqueId": unique_id,
                "account": account,
                "sharedKey": shared_key,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        unique_id = d.pop("uniqueId")

        account = d.pop("account")

        shared_key = d.pop("sharedKey")

        description = d.pop("description", UNSET)

        azure_storage_cloud_credentials_import_spec = cls(
            type_=type_,
            unique_id=unique_id,
            account=account,
            shared_key=shared_key,
            description=description,
        )

        azure_storage_cloud_credentials_import_spec.additional_properties = d
        return azure_storage_cloud_credentials_import_spec

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
