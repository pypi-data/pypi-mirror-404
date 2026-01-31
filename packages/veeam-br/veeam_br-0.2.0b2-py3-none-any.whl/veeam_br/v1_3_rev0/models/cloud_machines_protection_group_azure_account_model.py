from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudMachinesProtectionGroupAzureAccountModel")


@_attrs_define
class CloudMachinesProtectionGroupAzureAccountModel:
    """Azure account of cloud machine added to the protection group.

    Attributes:
        credentials_id (UUID | Unset): Credentials ID.
        account_type (EProtectionGroupCloudAccountType | Unset): Cloud account type.
        subscription_id (UUID | Unset): Subscription ID.
        region_id (str | Unset): ID of a region where the storage is located.
    """

    credentials_id: UUID | Unset = UNSET
    account_type: EProtectionGroupCloudAccountType | Unset = UNSET
    subscription_id: UUID | Unset = UNSET
    region_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        account_type: str | Unset = UNSET
        if not isinstance(self.account_type, Unset):
            account_type = self.account_type.value

        subscription_id: str | Unset = UNSET
        if not isinstance(self.subscription_id, Unset):
            subscription_id = str(self.subscription_id)

        region_id = self.region_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if account_type is not UNSET:
            field_dict["accountType"] = account_type
        if subscription_id is not UNSET:
            field_dict["subscriptionId"] = subscription_id
        if region_id is not UNSET:
            field_dict["regionId"] = region_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _account_type = d.pop("accountType", UNSET)
        account_type: EProtectionGroupCloudAccountType | Unset
        if isinstance(_account_type, Unset):
            account_type = UNSET
        else:
            account_type = EProtectionGroupCloudAccountType(_account_type)

        _subscription_id = d.pop("subscriptionId", UNSET)
        subscription_id: UUID | Unset
        if isinstance(_subscription_id, Unset):
            subscription_id = UNSET
        else:
            subscription_id = UUID(_subscription_id)

        region_id = d.pop("regionId", UNSET)

        cloud_machines_protection_group_azure_account_model = cls(
            credentials_id=credentials_id,
            account_type=account_type,
            subscription_id=subscription_id,
            region_id=region_id,
        )

        cloud_machines_protection_group_azure_account_model.additional_properties = d
        return cloud_machines_protection_group_azure_account_model

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
