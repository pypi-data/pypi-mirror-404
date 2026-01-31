from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_subscription_browser_model import AzureSubscriptionBrowserModel


T = TypeVar("T", bound="AzureComputeBrowserModel")


@_attrs_define
class AzureComputeBrowserModel:
    """Microsoft Azure compute account.

    Attributes:
        credentials_id (UUID): ID of the cloud credentials record.
        service_type (ECloudServiceType): Type of cloud service.
        region_type (str | Unset): Microsoft Azure region type.
        subscriptions (list[AzureSubscriptionBrowserModel] | Unset): Array of Microsoft Azure subscriptions associated
            with the account.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    region_type: str | Unset = UNSET
    subscriptions: list[AzureSubscriptionBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        region_type = self.region_type

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
                "credentialsId": credentials_id,
                "serviceType": service_type,
            }
        )
        if region_type is not UNSET:
            field_dict["regionType"] = region_type
        if subscriptions is not UNSET:
            field_dict["subscriptions"] = subscriptions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_subscription_browser_model import AzureSubscriptionBrowserModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        region_type = d.pop("regionType", UNSET)

        _subscriptions = d.pop("subscriptions", UNSET)
        subscriptions: list[AzureSubscriptionBrowserModel] | Unset = UNSET
        if _subscriptions is not UNSET:
            subscriptions = []
            for subscriptions_item_data in _subscriptions:
                subscriptions_item = AzureSubscriptionBrowserModel.from_dict(subscriptions_item_data)

                subscriptions.append(subscriptions_item)

        azure_compute_browser_model = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            region_type=region_type,
            subscriptions=subscriptions,
        )

        azure_compute_browser_model.additional_properties = d
        return azure_compute_browser_model

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
