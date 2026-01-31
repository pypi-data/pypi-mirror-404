from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel


T = TypeVar("T", bound="AmazonSnowballEdgeStorageBucketModel")


@_attrs_define
class AmazonSnowballEdgeStorageBucketModel:
    """Amazon S3 bucket.

    Attributes:
        bucket_name (str | Unset): Name of the Amazon S3 bucket.
        folder_name (str | Unset): Name of the folder to which the object storage repository is mapped.
        storage_consumption_limit (ObjectStorageConsumptionLimitModel | Unset): Soft consumption limit for the storage.
            The limit can be exceeded temporarily.
    """

    bucket_name: str | Unset = UNSET
    folder_name: str | Unset = UNSET
    storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bucket_name = self.bucket_name

        folder_name = self.folder_name

        storage_consumption_limit: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_consumption_limit, Unset):
            storage_consumption_limit = self.storage_consumption_limit.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bucket_name is not UNSET:
            field_dict["bucketName"] = bucket_name
        if folder_name is not UNSET:
            field_dict["folderName"] = folder_name
        if storage_consumption_limit is not UNSET:
            field_dict["storageConsumptionLimit"] = storage_consumption_limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_consumption_limit_model import ObjectStorageConsumptionLimitModel

        d = dict(src_dict)
        bucket_name = d.pop("bucketName", UNSET)

        folder_name = d.pop("folderName", UNSET)

        _storage_consumption_limit = d.pop("storageConsumptionLimit", UNSET)
        storage_consumption_limit: ObjectStorageConsumptionLimitModel | Unset
        if isinstance(_storage_consumption_limit, Unset):
            storage_consumption_limit = UNSET
        else:
            storage_consumption_limit = ObjectStorageConsumptionLimitModel.from_dict(_storage_consumption_limit)

        amazon_snowball_edge_storage_bucket_model = cls(
            bucket_name=bucket_name,
            folder_name=folder_name,
            storage_consumption_limit=storage_consumption_limit,
        )

        amazon_snowball_edge_storage_bucket_model.additional_properties = d
        return amazon_snowball_edge_storage_bucket_model

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
