from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VeeamDataCloudVaultModel")


@_attrs_define
class VeeamDataCloudVaultModel:
    """Veeam Data Cloud Vault repository.

    Attributes:
        vault_id (str): Vault ID.
        is_initialized (bool): If `true`, you have obtained a vault and assigned it to your backup server.
        vault_name (str | Unset): Vault repository name.
        storage_container_name (str | Unset): Storage container name.
        folders (list[str] | Unset): Array of folders located in Veeam Data Cloud Vault.
    """

    vault_id: str
    is_initialized: bool
    vault_name: str | Unset = UNSET
    storage_container_name: str | Unset = UNSET
    folders: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vault_id = self.vault_id

        is_initialized = self.is_initialized

        vault_name = self.vault_name

        storage_container_name = self.storage_container_name

        folders: list[str] | Unset = UNSET
        if not isinstance(self.folders, Unset):
            folders = self.folders

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vaultId": vault_id,
                "isInitialized": is_initialized,
            }
        )
        if vault_name is not UNSET:
            field_dict["vaultName"] = vault_name
        if storage_container_name is not UNSET:
            field_dict["storageContainerName"] = storage_container_name
        if folders is not UNSET:
            field_dict["folders"] = folders

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vault_id = d.pop("vaultId")

        is_initialized = d.pop("isInitialized")

        vault_name = d.pop("vaultName", UNSET)

        storage_container_name = d.pop("storageContainerName", UNSET)

        folders = cast(list[str], d.pop("folders", UNSET))

        veeam_data_cloud_vault_model = cls(
            vault_id=vault_id,
            is_initialized=is_initialized,
            vault_name=vault_name,
            storage_container_name=storage_container_name,
            folders=folders,
        )

        veeam_data_cloud_vault_model.additional_properties = d
        return veeam_data_cloud_vault_model

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
