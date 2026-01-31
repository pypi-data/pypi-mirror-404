from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ewan_accelerator_cache_size_unit import EWANAcceleratorCacheSizeUnit
from ..types import UNSET, Unset

T = TypeVar("T", bound="WANAcceleratorCacheModel")


@_attrs_define
class WANAcceleratorCacheModel:
    """Cache settings. Cache is used for storing service files (for source and target WAN accelerators) and global cache
    data (for target WAN accelerator).

        Attributes:
            cache_folder (str | Unset): Path to the cache folder.
            cache_size (int | Unset): Cache size.
            cache_size_unit (EWANAcceleratorCacheSizeUnit | Unset): Cache size unit.
    """

    cache_folder: str | Unset = UNSET
    cache_size: int | Unset = UNSET
    cache_size_unit: EWANAcceleratorCacheSizeUnit | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cache_folder = self.cache_folder

        cache_size = self.cache_size

        cache_size_unit: str | Unset = UNSET
        if not isinstance(self.cache_size_unit, Unset):
            cache_size_unit = self.cache_size_unit.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cache_folder is not UNSET:
            field_dict["cacheFolder"] = cache_folder
        if cache_size is not UNSET:
            field_dict["cacheSize"] = cache_size
        if cache_size_unit is not UNSET:
            field_dict["cacheSizeUnit"] = cache_size_unit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cache_folder = d.pop("cacheFolder", UNSET)

        cache_size = d.pop("cacheSize", UNSET)

        _cache_size_unit = d.pop("cacheSizeUnit", UNSET)
        cache_size_unit: EWANAcceleratorCacheSizeUnit | Unset
        if isinstance(_cache_size_unit, Unset):
            cache_size_unit = UNSET
        else:
            cache_size_unit = EWANAcceleratorCacheSizeUnit(_cache_size_unit)

        wan_accelerator_cache_model = cls(
            cache_folder=cache_folder,
            cache_size=cache_size,
            cache_size_unit=cache_size_unit,
        )

        wan_accelerator_cache_model.additional_properties = d
        return wan_accelerator_cache_model

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
