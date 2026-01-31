from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.azure_resource_group_browser_model import AzureResourceGroupBrowserModel
    from ..models.azure_storage_account_browser_model import AzureStorageAccountBrowserModel


T = TypeVar("T", bound="AzureLocationBrowserModel")


@_attrs_define
class AzureLocationBrowserModel:
    """Microsoft Azure location.

    Attributes:
        location (str): Location name.
        storage_accounts (list[AzureStorageAccountBrowserModel]): Array of storage accounts associated with the
            location.
        resource_groups (list[AzureResourceGroupBrowserModel]): Array of Azure resource groups.
    """

    location: str
    storage_accounts: list[AzureStorageAccountBrowserModel]
    resource_groups: list[AzureResourceGroupBrowserModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        location = self.location

        storage_accounts = []
        for storage_accounts_item_data in self.storage_accounts:
            storage_accounts_item = storage_accounts_item_data.to_dict()
            storage_accounts.append(storage_accounts_item)

        resource_groups = []
        for resource_groups_item_data in self.resource_groups:
            resource_groups_item = resource_groups_item_data.to_dict()
            resource_groups.append(resource_groups_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "location": location,
                "storageAccounts": storage_accounts,
                "resourceGroups": resource_groups,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_resource_group_browser_model import AzureResourceGroupBrowserModel
        from ..models.azure_storage_account_browser_model import AzureStorageAccountBrowserModel

        d = dict(src_dict)
        location = d.pop("location")

        storage_accounts = []
        _storage_accounts = d.pop("storageAccounts")
        for storage_accounts_item_data in _storage_accounts:
            storage_accounts_item = AzureStorageAccountBrowserModel.from_dict(storage_accounts_item_data)

            storage_accounts.append(storage_accounts_item)

        resource_groups = []
        _resource_groups = d.pop("resourceGroups")
        for resource_groups_item_data in _resource_groups:
            resource_groups_item = AzureResourceGroupBrowserModel.from_dict(resource_groups_item_data)

            resource_groups.append(resource_groups_item)

        azure_location_browser_model = cls(
            location=location,
            storage_accounts=storage_accounts,
            resource_groups=resource_groups,
        )

        azure_location_browser_model.additional_properties = d
        return azure_location_browser_model

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
