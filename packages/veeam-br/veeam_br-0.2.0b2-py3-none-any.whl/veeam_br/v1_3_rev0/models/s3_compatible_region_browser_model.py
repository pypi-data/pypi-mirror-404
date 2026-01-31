from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.s3_compatible_bucket_browser_model import S3CompatibleBucketBrowserModel


T = TypeVar("T", bound="S3CompatibleRegionBrowserModel")


@_attrs_define
class S3CompatibleRegionBrowserModel:
    """Region of S3 compatible storage.

    Attributes:
        id (str | Unset): Region ID.
        name (str | Unset): Region name.
        buckets (list[S3CompatibleBucketBrowserModel] | Unset): Array of buckets located in the region.
    """

    id: str | Unset = UNSET
    name: str | Unset = UNSET
    buckets: list[S3CompatibleBucketBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        buckets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.buckets, Unset):
            buckets = []
            for buckets_item_data in self.buckets:
                buckets_item = buckets_item_data.to_dict()
                buckets.append(buckets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if buckets is not UNSET:
            field_dict["buckets"] = buckets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.s3_compatible_bucket_browser_model import S3CompatibleBucketBrowserModel

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        _buckets = d.pop("buckets", UNSET)
        buckets: list[S3CompatibleBucketBrowserModel] | Unset = UNSET
        if _buckets is not UNSET:
            buckets = []
            for buckets_item_data in _buckets:
                buckets_item = S3CompatibleBucketBrowserModel.from_dict(buckets_item_data)

                buckets.append(buckets_item)

        s3_compatible_region_browser_model = cls(
            id=id,
            name=name,
            buckets=buckets,
        )

        s3_compatible_region_browser_model.additional_properties = d
        return s3_compatible_region_browser_model

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
