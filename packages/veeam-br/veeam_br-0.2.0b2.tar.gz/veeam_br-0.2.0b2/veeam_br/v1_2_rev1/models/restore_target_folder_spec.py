from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="RestoreTargetFolderSpec")


@_attrs_define
class RestoreTargetFolderSpec:
    """Destination VM folder.

    Attributes:
        folder (InventoryObjectModel): Inventory object properties.
        vm_name (str | Unset): Name of the restored VM. Note that if you do not specify a value for this property, Veeam
            Backup & Replication will use the original VM name.
        restore_vm_tags (bool | Unset): If `true`, Veeam Backup & Replication restores tags that were assigned to the
            original VMs, and assigns them to the restored VMs.
    """

    folder: InventoryObjectModel
    vm_name: str | Unset = UNSET
    restore_vm_tags: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        folder = self.folder.to_dict()

        vm_name = self.vm_name

        restore_vm_tags = self.restore_vm_tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "folder": folder,
            }
        )
        if vm_name is not UNSET:
            field_dict["vmName"] = vm_name
        if restore_vm_tags is not UNSET:
            field_dict["restoreVmTags"] = restore_vm_tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        folder = InventoryObjectModel.from_dict(d.pop("folder"))

        vm_name = d.pop("vmName", UNSET)

        restore_vm_tags = d.pop("restoreVmTags", UNSET)

        restore_target_folder_spec = cls(
            folder=folder,
            vm_name=vm_name,
            restore_vm_tags=restore_vm_tags,
        )

        restore_target_folder_spec.additional_properties = d
        return restore_target_folder_spec

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
