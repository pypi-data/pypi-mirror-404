from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.esmb_share_server_processing_mode import ESMBShareServerProcessingMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="SMBShareServerAdvancedSettingsModel")


@_attrs_define
class SMBShareServerAdvancedSettingsModel:
    r"""Advanced settings for SMB share.

    Attributes:
        processing_mode (ESMBShareServerProcessingMode | Unset): Processing mode for SMB share.
        direct_backup_failover_enabled (bool | Unset): If `true`, Veeam Backup & Replication will read data for backup
            directly from the file share when the snapshot is unavailable. Otherwise, the file share backup job will fail.
        storage_snapshot_path (str | Unset): Path in the `\\<server>\<snapshotfolder>\<snapshotname>` format to the
            snapshot stored on the SMB file share.
    """

    processing_mode: ESMBShareServerProcessingMode | Unset = UNSET
    direct_backup_failover_enabled: bool | Unset = UNSET
    storage_snapshot_path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        processing_mode: str | Unset = UNSET
        if not isinstance(self.processing_mode, Unset):
            processing_mode = self.processing_mode.value

        direct_backup_failover_enabled = self.direct_backup_failover_enabled

        storage_snapshot_path = self.storage_snapshot_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if processing_mode is not UNSET:
            field_dict["processingMode"] = processing_mode
        if direct_backup_failover_enabled is not UNSET:
            field_dict["directBackupFailoverEnabled"] = direct_backup_failover_enabled
        if storage_snapshot_path is not UNSET:
            field_dict["storageSnapshotPath"] = storage_snapshot_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _processing_mode = d.pop("processingMode", UNSET)
        processing_mode: ESMBShareServerProcessingMode | Unset
        if isinstance(_processing_mode, Unset):
            processing_mode = UNSET
        else:
            processing_mode = ESMBShareServerProcessingMode(_processing_mode)

        direct_backup_failover_enabled = d.pop("directBackupFailoverEnabled", UNSET)

        storage_snapshot_path = d.pop("storageSnapshotPath", UNSET)

        smb_share_server_advanced_settings_model = cls(
            processing_mode=processing_mode,
            direct_backup_failover_enabled=direct_backup_failover_enabled,
            storage_snapshot_path=storage_snapshot_path,
        )

        smb_share_server_advanced_settings_model.additional_properties = d
        return smb_share_server_advanced_settings_model

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
