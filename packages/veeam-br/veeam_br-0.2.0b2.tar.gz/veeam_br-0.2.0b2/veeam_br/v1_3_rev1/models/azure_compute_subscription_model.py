from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AzureComputeSubscriptionModel")


@_attrs_define
class AzureComputeSubscriptionModel:
    """Microsoft Azure compute subscription.

    Attributes:
        subscription_id (UUID): Subscription ID. To get the ID, run the [Get All Cloud
            Credentials](Credentials#operation/GetAllCloudCreds) request.
        location (str): Geographic location of Microsoft Azure datacenters. To optimize recovery speed, select a
            datacenter that is closest to the location of the backup.
    """

    subscription_id: UUID
    location: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscription_id = str(self.subscription_id)

        location = self.location

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subscriptionId": subscription_id,
                "location": location,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subscription_id = UUID(d.pop("subscriptionId"))

        location = d.pop("location")

        azure_compute_subscription_model = cls(
            subscription_id=subscription_id,
            location=location,
        )

        azure_compute_subscription_model.additional_properties = d
        return azure_compute_subscription_model

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
