from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.vi_vm_snapshot_replica_failback_folder_mapping_spec import (
        ViVMSnapshotReplicaFailbackFolderMappingSpec,
    )


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetFolderSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetFolderSpec:
    """Folders in the target datastores where all files of the recovered VMs will be stored.

    Attributes:
        restore_vm_tags (bool | Unset): If `true`, Veeam Backup & Replication restores tags that were assigned to the
            original VMs, and assigns them to the recovered VMs.
        folder_mapping (list[ViVMSnapshotReplicaFailbackFolderMappingSpec] | Unset): Array of restore points and target
            folders. To get a folder object, use the [Get Inventory Objects](Inventory-
            Browser#operation/GetInventoryObjects) request.
    """

    restore_vm_tags: bool | Unset = UNSET
    folder_mapping: list[ViVMSnapshotReplicaFailbackFolderMappingSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_vm_tags = self.restore_vm_tags

        folder_mapping: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.folder_mapping, Unset):
            folder_mapping = []
            for folder_mapping_item_data in self.folder_mapping:
                folder_mapping_item = folder_mapping_item_data.to_dict()
                folder_mapping.append(folder_mapping_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if restore_vm_tags is not UNSET:
            field_dict["restoreVMTags"] = restore_vm_tags
        if folder_mapping is not UNSET:
            field_dict["folderMapping"] = folder_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.vi_vm_snapshot_replica_failback_folder_mapping_spec import (
            ViVMSnapshotReplicaFailbackFolderMappingSpec,
        )

        d = dict(src_dict)
        restore_vm_tags = d.pop("restoreVMTags", UNSET)

        _folder_mapping = d.pop("folderMapping", UNSET)
        folder_mapping: list[ViVMSnapshotReplicaFailbackFolderMappingSpec] | Unset = UNSET
        if _folder_mapping is not UNSET:
            folder_mapping = []
            for folder_mapping_item_data in _folder_mapping:
                folder_mapping_item = ViVMSnapshotReplicaFailbackFolderMappingSpec.from_dict(folder_mapping_item_data)

                folder_mapping.append(folder_mapping_item)

        vi_vm_snapshot_replica_failback_target_folder_spec = cls(
            restore_vm_tags=restore_vm_tags,
            folder_mapping=folder_mapping,
        )

        vi_vm_snapshot_replica_failback_target_folder_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_folder_spec

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
