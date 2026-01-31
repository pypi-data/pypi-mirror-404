from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VeeamDataCloudVaultStorageBrowserFilters")


@_attrs_define
class VeeamDataCloudVaultStorageBrowserFilters:
    """Hierarchy filters for Veeam Data Cloud Vault. Using the filters reduces not only the number of records in the
    response body but also the response time.

        Attributes:
            vault_name (str): Filters vaults by vault name.
    """

    vault_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vault_name = self.vault_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vaultName": vault_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vault_name = d.pop("vaultName")

        veeam_data_cloud_vault_storage_browser_filters = cls(
            vault_name=vault_name,
        )

        veeam_data_cloud_vault_storage_browser_filters.additional_properties = d
        return veeam_data_cloud_vault_storage_browser_filters

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
