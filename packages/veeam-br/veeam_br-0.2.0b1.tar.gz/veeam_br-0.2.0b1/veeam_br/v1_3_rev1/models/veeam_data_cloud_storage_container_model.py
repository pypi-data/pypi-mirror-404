from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel
    from ..models.object_storage_immutability_model import ObjectStorageImmutabilityModel


T = TypeVar("T", bound="VeeamDataCloudStorageContainerModel")


@_attrs_define
class VeeamDataCloudStorageContainerModel:
    """Veeam Data Cloud container.

    Attributes:
        folder (str): Folder used to store data.
        immutability (ObjectStorageImmutabilityModel): Object storage immutability.
        storage_consumption_limit (ObjectStorageConsumptionLimitModel | Unset): Soft consumption limit for the storage.
            The limit can be exceeded temporarily.
    """

    folder: str
    immutability: ObjectStorageImmutabilityModel
    storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        folder = self.folder

        immutability = self.immutability.to_dict()

        storage_consumption_limit: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_consumption_limit, Unset):
            storage_consumption_limit = self.storage_consumption_limit.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "folder": folder,
                "immutability": immutability,
            }
        )
        if storage_consumption_limit is not UNSET:
            field_dict["storageConsumptionLimit"] = storage_consumption_limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel
        from ..models.object_storage_immutability_model import ObjectStorageImmutabilityModel

        d = dict(src_dict)
        folder = d.pop("folder")

        immutability = ObjectStorageImmutabilityModel.from_dict(d.pop("immutability"))

        _storage_consumption_limit = d.pop("storageConsumptionLimit", UNSET)
        storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset
        if isinstance(_storage_consumption_limit, Unset):
            storage_consumption_limit = UNSET
        else:
            storage_consumption_limit = ObjectStorageConsumptionLimitModel.from_dict(_storage_consumption_limit)

        veeam_data_cloud_storage_container_model = cls(
            folder=folder,
            immutability=immutability,
            storage_consumption_limit=storage_consumption_limit,
        )

        veeam_data_cloud_storage_container_model.additional_properties = d
        return veeam_data_cloud_storage_container_model

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
