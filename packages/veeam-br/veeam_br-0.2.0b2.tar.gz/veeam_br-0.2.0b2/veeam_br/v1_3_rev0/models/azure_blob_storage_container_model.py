from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel
    from ..models.object_storage_immutability_model import ObjectStorageImmutabilityModel


T = TypeVar("T", bound="AzureBlobStorageContainerModel")


@_attrs_define
class AzureBlobStorageContainerModel:
    """Azure Blob storage container.

    Attributes:
        container_name (str): Container name.
        folder_name (str): Name of the folder to which the object storage repository is mapped.
        storage_consumption_limit (ObjectStorageConsumptionLimitModel | Unset): Soft consumption limit for the storage.
            The limit can be exceeded temporarily.
        immutability (ObjectStorageImmutabilityModel | Unset): Object storage immutability.
    """

    container_name: str
    folder_name: str
    storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset = UNSET
    immutability: ObjectStorageImmutabilityModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        container_name = self.container_name

        folder_name = self.folder_name

        storage_consumption_limit: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_consumption_limit, Unset):
            storage_consumption_limit = self.storage_consumption_limit.to_dict()

        immutability: dict[str, Any] | Unset = UNSET
        if not isinstance(self.immutability, Unset):
            immutability = self.immutability.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "containerName": container_name,
                "folderName": folder_name,
            }
        )
        if storage_consumption_limit is not UNSET:
            field_dict["storageConsumptionLimit"] = storage_consumption_limit
        if immutability is not UNSET:
            field_dict["immutability"] = immutability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel
        from ..models.object_storage_immutability_model import ObjectStorageImmutabilityModel

        d = dict(src_dict)
        container_name = d.pop("containerName")

        folder_name = d.pop("folderName")

        _storage_consumption_limit = d.pop("storageConsumptionLimit", UNSET)
        storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset
        if isinstance(_storage_consumption_limit, Unset):
            storage_consumption_limit = UNSET
        else:
            storage_consumption_limit = ObjectStorageConsumptionLimitModel.from_dict(_storage_consumption_limit)

        _immutability = d.pop("immutability", UNSET)
        immutability: ObjectStorageImmutabilityModel | Unset
        if isinstance(_immutability, Unset):
            immutability = UNSET
        else:
            immutability = ObjectStorageImmutabilityModel.from_dict(_immutability)

        azure_blob_storage_container_model = cls(
            container_name=container_name,
            folder_name=folder_name,
            storage_consumption_limit=storage_consumption_limit,
            immutability=immutability,
        )

        azure_blob_storage_container_model.additional_properties = d
        return azure_blob_storage_container_model

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
