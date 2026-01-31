from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureStorageAccountBrowserModel")


@_attrs_define
class AzureStorageAccountBrowserModel:
    """
    Attributes:
        storage_account_name (str | Unset): Account name.
        instance_sizes (list[str] | Unset): Array of available instance sizes.
    """

    storage_account_name: str | Unset = UNSET
    instance_sizes: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage_account_name = self.storage_account_name

        instance_sizes: list[str] | Unset = UNSET
        if not isinstance(self.instance_sizes, Unset):
            instance_sizes = self.instance_sizes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if storage_account_name is not UNSET:
            field_dict["storageAccountName"] = storage_account_name
        if instance_sizes is not UNSET:
            field_dict["instanceSizes"] = instance_sizes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        storage_account_name = d.pop("storageAccountName", UNSET)

        instance_sizes = cast(list[str], d.pop("instanceSizes", UNSET))

        azure_storage_account_browser_model = cls(
            storage_account_name=storage_account_name,
            instance_sizes=instance_sizes,
        )

        azure_storage_account_browser_model.additional_properties = d
        return azure_storage_account_browser_model

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
