from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeCloudCredentialsSubscriptionInfo")


@_attrs_define
class AzureComputeCloudCredentialsSubscriptionInfo:
    """Azure subscriptions associated with Azure compute account.

    Attributes:
        id (UUID): ID that Veeam Backup & Replication assigned to the Azure subscription.
        azure_subscription_id (str): Original Azure subscription ID.
        azure_subscription_name (str | Unset): Azure subscription name.
    """

    id: UUID
    azure_subscription_id: str
    azure_subscription_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        azure_subscription_id = self.azure_subscription_id

        azure_subscription_name = self.azure_subscription_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "azureSubscriptionId": azure_subscription_id,
            }
        )
        if azure_subscription_name is not UNSET:
            field_dict["azureSubscriptionName"] = azure_subscription_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        azure_subscription_id = d.pop("azureSubscriptionId")

        azure_subscription_name = d.pop("azureSubscriptionName", UNSET)

        azure_compute_cloud_credentials_subscription_info = cls(
            id=id,
            azure_subscription_id=azure_subscription_id,
            azure_subscription_name=azure_subscription_name,
        )

        azure_compute_cloud_credentials_subscription_info.additional_properties = d
        return azure_compute_cloud_credentials_subscription_info

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
