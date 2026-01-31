from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureStorageCloudCredentialsModel")


@_attrs_define
class AzureStorageCloudCredentialsModel:
    """
    Attributes:
        id (UUID): ID of the cloud credentials record.
        type_ (ECloudCredentialsType): Cloud credentials type.
        account (str): Name of the Azure storage account.
        description (str | Unset): Description of the cloud credentials record.
        unique_id (str | Unset): Unique ID that identifies the cloud credentials record.
    """

    id: UUID
    type_: ECloudCredentialsType
    account: str
    description: str | Unset = UNSET
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        account = self.account

        description = self.description

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "account": account,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ECloudCredentialsType(d.pop("type"))

        account = d.pop("account")

        description = d.pop("description", UNSET)

        unique_id = d.pop("uniqueId", UNSET)

        azure_storage_cloud_credentials_model = cls(
            id=id,
            type_=type_,
            account=account,
            description=description,
            unique_id=unique_id,
        )

        azure_storage_cloud_credentials_model.additional_properties = d
        return azure_storage_cloud_credentials_model

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
