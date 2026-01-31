from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeBrowserFilters")


@_attrs_define
class AzureComputeBrowserFilters:
    """Azure Compute hierarchy filters. Using the filters reduces not only the number of records in the response body but
    also the response time.

        Attributes:
            show_all_storage_accounts (bool | Unset): If `true`, the result contains compute resorces for all storage
                accounts. If *false*, the result contains compute resorces available for the specified storage account only.
                Default: False.
            subscription_id (str | Unset): Filters compute resorces by ID that Veeam Backup & Replication assigned to the
                Azure subscription.
            location (str | Unset): Filters compute resorces by Azure location name.
            has_networks (bool | Unset): If `true`, the result contains Azure resource groups with virtual networks only.
                Default: False.
    """

    show_all_storage_accounts: bool | Unset = False
    subscription_id: str | Unset = UNSET
    location: str | Unset = UNSET
    has_networks: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        show_all_storage_accounts = self.show_all_storage_accounts

        subscription_id = self.subscription_id

        location = self.location

        has_networks = self.has_networks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if show_all_storage_accounts is not UNSET:
            field_dict["showAllStorageAccounts"] = show_all_storage_accounts
        if subscription_id is not UNSET:
            field_dict["subscriptionId"] = subscription_id
        if location is not UNSET:
            field_dict["location"] = location
        if has_networks is not UNSET:
            field_dict["hasNetworks"] = has_networks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        show_all_storage_accounts = d.pop("showAllStorageAccounts", UNSET)

        subscription_id = d.pop("subscriptionId", UNSET)

        location = d.pop("location", UNSET)

        has_networks = d.pop("hasNetworks", UNSET)

        azure_compute_browser_filters = cls(
            show_all_storage_accounts=show_all_storage_accounts,
            subscription_id=subscription_id,
            location=location,
            has_networks=has_networks,
        )

        azure_compute_browser_filters.additional_properties = d
        return azure_compute_browser_filters

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
