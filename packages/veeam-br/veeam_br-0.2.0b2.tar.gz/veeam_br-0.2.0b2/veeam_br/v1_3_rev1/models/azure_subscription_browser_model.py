from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_location_browser_model import AzureLocationBrowserModel


T = TypeVar("T", bound="AzureSubscriptionBrowserModel")


@_attrs_define
class AzureSubscriptionBrowserModel:
    """Microsoft Azure subscription.

    Attributes:
        id (UUID): ID that Veeam Backup & Replication assigned to the Microsoft Azure subscription.
        azure_subscription_id (str | Unset): Original Microsoft Azure subscription ID. For more information, see
            [Microsoft documentation](https://learn.microsoft.com/en-us/azure/azure-portal/get-subscription-tenant-id#find-
            your-azure-subscription).
        locations (list[AzureLocationBrowserModel] | Unset): Array of Microsoft Azure geographic regions.
    """

    id: UUID
    azure_subscription_id: str | Unset = UNSET
    locations: list[AzureLocationBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        azure_subscription_id = self.azure_subscription_id

        locations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.locations, Unset):
            locations = []
            for locations_item_data in self.locations:
                locations_item = locations_item_data.to_dict()
                locations.append(locations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if azure_subscription_id is not UNSET:
            field_dict["azureSubscriptionId"] = azure_subscription_id
        if locations is not UNSET:
            field_dict["locations"] = locations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_location_browser_model import AzureLocationBrowserModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        azure_subscription_id = d.pop("azureSubscriptionId", UNSET)

        _locations = d.pop("locations", UNSET)
        locations: list[AzureLocationBrowserModel] | Unset = UNSET
        if _locations is not UNSET:
            locations = []
            for locations_item_data in _locations:
                locations_item = AzureLocationBrowserModel.from_dict(locations_item_data)

                locations.append(locations_item)

        azure_subscription_browser_model = cls(
            id=id,
            azure_subscription_id=azure_subscription_id,
            locations=locations,
        )

        azure_subscription_browser_model.additional_properties = d
        return azure_subscription_browser_model

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
