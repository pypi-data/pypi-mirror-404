from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonS3GlacierStorageBucketModel")


@_attrs_define
class AmazonS3GlacierStorageBucketModel:
    """Amazon S3 Glacier bucket where backup data is stored.

    Attributes:
        region_id (str): ID of a region where the Amazon S3 bucket is located.
        bucket_name (str): Name of an Amazon S3 Glacier bucket.
        folder_name (str): Name of the folder that the object storage repository is mapped to.
        immutability_enabled (bool | Unset): If `true`, storage immutability is enabled.
        use_deep_archive (bool | Unset): If `true`, Glacier Deep Archive is used for backups with the retention policy
            over 180 days.
    """

    region_id: str
    bucket_name: str
    folder_name: str
    immutability_enabled: bool | Unset = UNSET
    use_deep_archive: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        region_id = self.region_id

        bucket_name = self.bucket_name

        folder_name = self.folder_name

        immutability_enabled = self.immutability_enabled

        use_deep_archive = self.use_deep_archive

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "regionId": region_id,
                "bucketName": bucket_name,
                "folderName": folder_name,
            }
        )
        if immutability_enabled is not UNSET:
            field_dict["immutabilityEnabled"] = immutability_enabled
        if use_deep_archive is not UNSET:
            field_dict["useDeepArchive"] = use_deep_archive

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        region_id = d.pop("regionId")

        bucket_name = d.pop("bucketName")

        folder_name = d.pop("folderName")

        immutability_enabled = d.pop("immutabilityEnabled", UNSET)

        use_deep_archive = d.pop("useDeepArchive", UNSET)

        amazon_s3_glacier_storage_bucket_model = cls(
            region_id=region_id,
            bucket_name=bucket_name,
            folder_name=folder_name,
            immutability_enabled=immutability_enabled,
            use_deep_archive=use_deep_archive,
        )

        amazon_s3_glacier_storage_bucket_model.additional_properties = d
        return amazon_s3_glacier_storage_bucket_model

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
