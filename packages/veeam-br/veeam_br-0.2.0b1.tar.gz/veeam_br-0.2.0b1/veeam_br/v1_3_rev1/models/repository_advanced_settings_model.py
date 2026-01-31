from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_rotated_drive_cleanup_mode import ERotatedDriveCleanupMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryAdvancedSettingsModel")


@_attrs_define
class RepositoryAdvancedSettingsModel:
    """Advanced settings for the backup repository.

    Attributes:
        align_data_blocks (bool | Unset): If `true`, Veeam Backup & Replication aligns VM data saved to a backup file at
            a 4 KB block boundary.
        decompress_before_storing (bool | Unset): If `true`, Veeam Backup & Replication decompresses backup data blocks
            before storing to improve deduplication ratios.
        rotated_drives (bool | Unset): If `true`, the repository drive is rotated.
        per_vm_backup (bool | Unset): If `true`, Veeam Backup & Replication creates a separate backup file for every VM
            in the job.<p> Consider the following&#58;<p> <ul> <li>For repositories created after Veeam Backup & Replication
            13, the value is always set to `true`.</li> <li> For repositories created before Veeam Backup & Replication 13,
            the behavior depends on the value that is already selected. <ul> <li>If `perVMBackup` is set to `true`, you
            cannot set it to `false`.</li> <li>If `perVMBackup` is set to `false`, you can set it to `true`, but you cannot
            set it back to `false`.</li> </ul> </li> </ul>
        rotated_drive_cleanup_mode (ERotatedDriveCleanupMode | Unset): Cleanup mode:<ul> <li>`Disabled` — continue the
            backup chain on an inserted drive.</li> <li>`ClearBackupFolder` — delete existing backups belonging to the
            job.</li> <li>`ClearRepositoryFolder` — delete all existing backups from repository.</li></ul>
    """

    align_data_blocks: bool | Unset = UNSET
    decompress_before_storing: bool | Unset = UNSET
    rotated_drives: bool | Unset = UNSET
    per_vm_backup: bool | Unset = UNSET
    rotated_drive_cleanup_mode: ERotatedDriveCleanupMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        align_data_blocks = self.align_data_blocks

        decompress_before_storing = self.decompress_before_storing

        rotated_drives = self.rotated_drives

        per_vm_backup = self.per_vm_backup

        rotated_drive_cleanup_mode: str | Unset = UNSET
        if not isinstance(self.rotated_drive_cleanup_mode, Unset):
            rotated_drive_cleanup_mode = self.rotated_drive_cleanup_mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if align_data_blocks is not UNSET:
            field_dict["alignDataBlocks"] = align_data_blocks
        if decompress_before_storing is not UNSET:
            field_dict["decompressBeforeStoring"] = decompress_before_storing
        if rotated_drives is not UNSET:
            field_dict["rotatedDrives"] = rotated_drives
        if per_vm_backup is not UNSET:
            field_dict["perVmBackup"] = per_vm_backup
        if rotated_drive_cleanup_mode is not UNSET:
            field_dict["RotatedDriveCleanupMode"] = rotated_drive_cleanup_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        align_data_blocks = d.pop("alignDataBlocks", UNSET)

        decompress_before_storing = d.pop("decompressBeforeStoring", UNSET)

        rotated_drives = d.pop("rotatedDrives", UNSET)

        per_vm_backup = d.pop("perVmBackup", UNSET)

        _rotated_drive_cleanup_mode = d.pop("RotatedDriveCleanupMode", UNSET)
        rotated_drive_cleanup_mode: ERotatedDriveCleanupMode | Unset
        if isinstance(_rotated_drive_cleanup_mode, Unset):
            rotated_drive_cleanup_mode = UNSET
        else:
            rotated_drive_cleanup_mode = ERotatedDriveCleanupMode(_rotated_drive_cleanup_mode)

        repository_advanced_settings_model = cls(
            align_data_blocks=align_data_blocks,
            decompress_before_storing=decompress_before_storing,
            rotated_drives=rotated_drives,
            per_vm_backup=per_vm_backup,
            rotated_drive_cleanup_mode=rotated_drive_cleanup_mode,
        )

        repository_advanced_settings_model.additional_properties = d
        return repository_advanced_settings_model

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
