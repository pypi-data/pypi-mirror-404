from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_cloud_credentials_subscription_info import AzureComputeCloudCredentialsSubscriptionInfo


T = TypeVar("T", bound="AzureComputeCloudCredentialsSubscriptionModel")


@_attrs_define
class AzureComputeCloudCredentialsSubscriptionModel:
    """Microsoft Azure tenant settings.

    Attributes:
        tenant_id (str): ID of a tenant where the Microsoft Entra ID application is registered in.
        application_id (str): Client ID assigned to the Microsoft Entra ID application.
        secret (str | Unset): (For password-based authentication) Client secret assigned to the Microsoft Entra ID
            application.
        subscriptions (list[AzureComputeCloudCredentialsSubscriptionInfo] | Unset): Array of Azure subscriptions
            associated with the account.
    """

    tenant_id: str
    application_id: str
    secret: str | Unset = UNSET
    subscriptions: list[AzureComputeCloudCredentialsSubscriptionInfo] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        application_id = self.application_id

        secret = self.secret

        subscriptions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.subscriptions, Unset):
            subscriptions = []
            for subscriptions_item_data in self.subscriptions:
                subscriptions_item = subscriptions_item_data.to_dict()
                subscriptions.append(subscriptions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenantId": tenant_id,
                "applicationId": application_id,
            }
        )
        if secret is not UNSET:
            field_dict["secret"] = secret
        if subscriptions is not UNSET:
            field_dict["subscriptions"] = subscriptions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_cloud_credentials_subscription_info import (
            AzureComputeCloudCredentialsSubscriptionInfo,
        )

        d = dict(src_dict)
        tenant_id = d.pop("tenantId")

        application_id = d.pop("applicationId")

        secret = d.pop("secret", UNSET)

        _subscriptions = d.pop("subscriptions", UNSET)
        subscriptions: list[AzureComputeCloudCredentialsSubscriptionInfo] | Unset = UNSET
        if _subscriptions is not UNSET:
            subscriptions = []
            for subscriptions_item_data in _subscriptions:
                subscriptions_item = AzureComputeCloudCredentialsSubscriptionInfo.from_dict(subscriptions_item_data)

                subscriptions.append(subscriptions_item)

        azure_compute_cloud_credentials_subscription_model = cls(
            tenant_id=tenant_id,
            application_id=application_id,
            secret=secret,
            subscriptions=subscriptions,
        )

        azure_compute_cloud_credentials_subscription_model.additional_properties = d
        return azure_compute_cloud_credentials_subscription_model

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
