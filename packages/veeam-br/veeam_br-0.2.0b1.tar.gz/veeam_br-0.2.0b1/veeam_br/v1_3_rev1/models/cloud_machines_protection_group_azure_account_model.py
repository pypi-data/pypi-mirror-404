from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType

T = TypeVar("T", bound="CloudMachinesProtectionGroupAzureAccountModel")


@_attrs_define
class CloudMachinesProtectionGroupAzureAccountModel:
    """Microsoft Azure account of cloud machine added to the protection group.

    Attributes:
        account_type (EProtectionGroupCloudAccountType): Cloud account type.
        subscription_id (UUID): Subscription ID.
        region_type (EAzureRegionType): Microsoft Azure region.
        region_id (str): ID of a region where the storage is located.
    """

    account_type: EProtectionGroupCloudAccountType
    subscription_id: UUID
    region_type: EAzureRegionType
    region_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        account_type = self.account_type.value

        subscription_id = str(self.subscription_id)

        region_type = self.region_type.value

        region_id = self.region_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accountType": account_type,
                "subscriptionId": subscription_id,
                "regionType": region_type,
                "regionId": region_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_type = EProtectionGroupCloudAccountType(d.pop("accountType"))

        subscription_id = UUID(d.pop("subscriptionId"))

        region_type = EAzureRegionType(d.pop("regionType"))

        region_id = d.pop("regionId")

        cloud_machines_protection_group_azure_account_model = cls(
            account_type=account_type,
            subscription_id=subscription_id,
            region_type=region_type,
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
