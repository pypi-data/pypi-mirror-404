from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureArchiveStorageContainerModel")


@_attrs_define
class AzureArchiveStorageContainerModel:
    """Azure Archive container where backup data is stored.

    Attributes:
        container_name (str): Name of an Azure Archive container.
        folder_name (str): Name of the folder to which the object storage repository is mapped.
        immutability_enabled (bool | Unset): If `true`, immutability is enabled for the container.
    """

    container_name: str
    folder_name: str
    immutability_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        container_name = self.container_name

        folder_name = self.folder_name

        immutability_enabled = self.immutability_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "containerName": container_name,
                "folderName": folder_name,
            }
        )
        if immutability_enabled is not UNSET:
            field_dict["immutabilityEnabled"] = immutability_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        container_name = d.pop("containerName")

        folder_name = d.pop("folderName")

        immutability_enabled = d.pop("immutabilityEnabled", UNSET)

        azure_archive_storage_container_model = cls(
            container_name=container_name,
            folder_name=folder_name,
            immutability_enabled=immutability_enabled,
        )

        azure_archive_storage_container_model.additional_properties = d
        return azure_archive_storage_container_model

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
