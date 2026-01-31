from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel


T = TypeVar("T", bound="GoogleCloudStorageBucketModel")


@_attrs_define
class GoogleCloudStorageBucketModel:
    """Google Cloud object storage bucket where backup data is stored.

    Attributes:
        bucket_name (str): Name of a Google Cloud bucket.
        folder_name (str): Name of the folder that the object storage repository is mapped to.
        storage_consumption_limit (ObjectStorageConsumptionLimitModel | Unset): Soft consumption limit for the storage.
            The limit can be exceeded temporarily.
        nearline_storage_enabled (bool | Unset): If `true`, the nearline storage class is used.
    """

    bucket_name: str
    folder_name: str
    storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset = UNSET
    nearline_storage_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bucket_name = self.bucket_name

        folder_name = self.folder_name

        storage_consumption_limit: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_consumption_limit, Unset):
            storage_consumption_limit = self.storage_consumption_limit.to_dict()

        nearline_storage_enabled = self.nearline_storage_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bucketName": bucket_name,
                "folderName": folder_name,
            }
        )
        if storage_consumption_limit is not UNSET:
            field_dict["storageConsumptionLimit"] = storage_consumption_limit
        if nearline_storage_enabled is not UNSET:
            field_dict["nearlineStorageEnabled"] = nearline_storage_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel

        d = dict(src_dict)
        bucket_name = d.pop("bucketName")

        folder_name = d.pop("folderName")

        _storage_consumption_limit = d.pop("storageConsumptionLimit", UNSET)
        storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset
        if isinstance(_storage_consumption_limit, Unset):
            storage_consumption_limit = UNSET
        else:
            storage_consumption_limit = ObjectStorageConsumptionLimitModel.from_dict(_storage_consumption_limit)

        nearline_storage_enabled = d.pop("nearlineStorageEnabled", UNSET)

        google_cloud_storage_bucket_model = cls(
            bucket_name=bucket_name,
            folder_name=folder_name,
            storage_consumption_limit=storage_consumption_limit,
            nearline_storage_enabled=nearline_storage_enabled,
        )

        google_cloud_storage_bucket_model.additional_properties = d
        return google_cloud_storage_bucket_model

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
