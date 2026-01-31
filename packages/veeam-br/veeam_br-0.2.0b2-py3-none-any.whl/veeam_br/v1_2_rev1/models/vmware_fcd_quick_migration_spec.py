from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VmwareFcdQuickMigrationSpec")


@_attrs_define
class VmwareFcdQuickMigrationSpec:
    """
    Attributes:
        target_datastore (InventoryObjectModel): Inventory object properties.
        mounted_disk_names (list[str] | Unset): Array of disks that will be migrated to the `targetDatastore` associated
            with the `storagePolicy`.
        storage_policy (InventoryObjectModel | Unset): Inventory object properties.
    """

    target_datastore: InventoryObjectModel
    mounted_disk_names: list[str] | Unset = UNSET
    storage_policy: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        target_datastore = self.target_datastore.to_dict()

        mounted_disk_names: list[str] | Unset = UNSET
        if not isinstance(self.mounted_disk_names, Unset):
            mounted_disk_names = self.mounted_disk_names

        storage_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_policy, Unset):
            storage_policy = self.storage_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "targetDatastore": target_datastore,
            }
        )
        if mounted_disk_names is not UNSET:
            field_dict["mountedDiskNames"] = mounted_disk_names
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        target_datastore = InventoryObjectModel.from_dict(d.pop("targetDatastore"))

        mounted_disk_names = cast(list[str], d.pop("mountedDiskNames", UNSET))

        _storage_policy = d.pop("storagePolicy", UNSET)
        storage_policy: InventoryObjectModel | Unset
        if isinstance(_storage_policy, Unset):
            storage_policy = UNSET
        else:
            storage_policy = InventoryObjectModel.from_dict(_storage_policy)

        vmware_fcd_quick_migration_spec = cls(
            target_datastore=target_datastore,
            mounted_disk_names=mounted_disk_names,
            storage_policy=storage_policy,
        )

        vmware_fcd_quick_migration_spec.additional_properties = d
        return vmware_fcd_quick_migration_spec

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
