from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VmwareFcdWriteCacheSpec")


@_attrs_define
class VmwareFcdWriteCacheSpec:
    """Write cache for recovered disks.

    Attributes:
        redirect_is_enabled (bool): If `true`, cache redirection is enabled. In this case, all changes made to the
            recovered disks while the Instant FCD Recovery is active are redirected to the specified `cacheDatastore`
            associated with the `storagePolicy`.
        cache_datastore (InventoryObjectModel | Unset): Inventory object properties.
        storage_policy (InventoryObjectModel | Unset): Inventory object properties.
    """

    redirect_is_enabled: bool
    cache_datastore: InventoryObjectModel | Unset = UNSET
    storage_policy: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        redirect_is_enabled = self.redirect_is_enabled

        cache_datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cache_datastore, Unset):
            cache_datastore = self.cache_datastore.to_dict()

        storage_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_policy, Unset):
            storage_policy = self.storage_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "redirectIsEnabled": redirect_is_enabled,
            }
        )
        if cache_datastore is not UNSET:
            field_dict["cacheDatastore"] = cache_datastore
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        redirect_is_enabled = d.pop("redirectIsEnabled")

        _cache_datastore = d.pop("cacheDatastore", UNSET)
        cache_datastore: InventoryObjectModel | Unset
        if isinstance(_cache_datastore, Unset):
            cache_datastore = UNSET
        else:
            cache_datastore = InventoryObjectModel.from_dict(_cache_datastore)

        _storage_policy = d.pop("storagePolicy", UNSET)
        storage_policy: InventoryObjectModel | Unset
        if isinstance(_storage_policy, Unset):
            storage_policy = UNSET
        else:
            storage_policy = InventoryObjectModel.from_dict(_storage_policy)

        vmware_fcd_write_cache_spec = cls(
            redirect_is_enabled=redirect_is_enabled,
            cache_datastore=cache_datastore,
            storage_policy=storage_policy,
        )

        vmware_fcd_write_cache_spec.additional_properties = d
        return vmware_fcd_write_cache_spec

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
