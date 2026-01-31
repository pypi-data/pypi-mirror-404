from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GoogleCloudStorageBrowserFilters")


@_attrs_define
class GoogleCloudStorageBrowserFilters:
    """Google Cloud hierarchy filters. Using the filters reduces not only the number of records in the response body but
    also the response time.

        Attributes:
            region_id (str): Google Cloud data center region.
            bucket_name (str | Unset): Bucket name.
    """

    region_id: str
    bucket_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        region_id = self.region_id

        bucket_name = self.bucket_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "regionId": region_id,
            }
        )
        if bucket_name is not UNSET:
            field_dict["bucketName"] = bucket_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        region_id = d.pop("regionId")

        bucket_name = d.pop("bucketName", UNSET)

        google_cloud_storage_browser_filters = cls(
            region_id=region_id,
            bucket_name=bucket_name,
        )

        google_cloud_storage_browser_filters.additional_properties = d
        return google_cloud_storage_browser_filters

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
