from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.wan_accelerator_cache_model import WANAcceleratorCacheModel
    from ..models.wan_accelerator_server_model import WANAcceleratorServerModel


T = TypeVar("T", bound="WANAcceleratorSpec")


@_attrs_define
class WANAcceleratorSpec:
    """
    Attributes:
        server (WANAcceleratorServerModel | Unset): Microsoft Windows server used as a WAN accelerator.
        cache (WANAcceleratorCacheModel | Unset): Cache settings. Cache is used for storing service files (for source
            and target WAN accelerators) and global cache data (for target WAN accelerator).
    """

    server: WANAcceleratorServerModel | Unset = UNSET
    cache: WANAcceleratorCacheModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        server: dict[str, Any] | Unset = UNSET
        if not isinstance(self.server, Unset):
            server = self.server.to_dict()

        cache: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cache, Unset):
            cache = self.cache.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if server is not UNSET:
            field_dict["server"] = server
        if cache is not UNSET:
            field_dict["cache"] = cache

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.wan_accelerator_cache_model import WANAcceleratorCacheModel
        from ..models.wan_accelerator_server_model import WANAcceleratorServerModel

        d = dict(src_dict)
        _server = d.pop("server", UNSET)
        server: WANAcceleratorServerModel | Unset
        if isinstance(_server, Unset):
            server = UNSET
        else:
            server = WANAcceleratorServerModel.from_dict(_server)

        _cache = d.pop("cache", UNSET)
        cache: WANAcceleratorCacheModel | Unset
        if isinstance(_cache, Unset):
            cache = UNSET
        else:
            cache = WANAcceleratorCacheModel.from_dict(_cache)

        wan_accelerator_spec = cls(
            server=server,
            cache=cache,
        )

        wan_accelerator_spec.additional_properties = d
        return wan_accelerator_spec

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
