from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureDataBoxStorageContainerModel")


@_attrs_define
class AzureDataBoxStorageContainerModel:
    """Azure Data Box container where backup data is stored.

    Attributes:
        container_name (str | Unset): Container name.
        folder_name (str | Unset): Name of the folder that the object storage repository is mapped to.
    """

    container_name: str | Unset = UNSET
    folder_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        container_name = self.container_name

        folder_name = self.folder_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if container_name is not UNSET:
            field_dict["containerName"] = container_name
        if folder_name is not UNSET:
            field_dict["folderName"] = folder_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        container_name = d.pop("containerName", UNSET)

        folder_name = d.pop("folderName", UNSET)

        azure_data_box_storage_container_model = cls(
            container_name=container_name,
            folder_name=folder_name,
        )

        azure_data_box_storage_container_model.additional_properties = d
        return azure_data_box_storage_container_model

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
