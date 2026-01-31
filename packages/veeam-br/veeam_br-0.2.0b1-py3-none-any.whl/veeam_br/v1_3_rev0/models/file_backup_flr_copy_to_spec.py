from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_file_backup_flr_copy_to_restore_mode import EFileBackupFLRCopyToRestoreMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="FileBackupFLRCopyToSpec")


@_attrs_define
class FileBackupFLRCopyToSpec:
    """Settings for copying file system items.

    Attributes:
        source_path (list[str]): Array of paths to the items that you want to restore.
        restore_mode (EFileBackupFLRCopyToRestoreMode): Restore mode.
        is_recursive (bool | Unset): If `true`, all files and folders in the source path are copied recursively.
        to_date_time (datetime.datetime | Unset): Date when the restore point was created. Use this property when
            copying files and folders from an erlier restore point (the `restoreMode` value is `Custom`).
        unstructured_data_server_id (UUID | Unset): ID of a server where the target shared folder is located. Use this
            property when copying files and folders to a file share.
        path (str | Unset): Path to the target folder.
        copy_to_backup_server (bool | Unset): If `true`, the files and folders are copied to a folder on the machine
            where the Veeam Backup & Replication console is installed.
        restore_permissions (bool | Unset): If `true`, Veeam Backup & Replication will restore permissions and security
            attributes of the backups.
    """

    source_path: list[str]
    restore_mode: EFileBackupFLRCopyToRestoreMode
    is_recursive: bool | Unset = UNSET
    to_date_time: datetime.datetime | Unset = UNSET
    unstructured_data_server_id: UUID | Unset = UNSET
    path: str | Unset = UNSET
    copy_to_backup_server: bool | Unset = UNSET
    restore_permissions: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_path = self.source_path

        restore_mode = self.restore_mode.value

        is_recursive = self.is_recursive

        to_date_time: str | Unset = UNSET
        if not isinstance(self.to_date_time, Unset):
            to_date_time = self.to_date_time.isoformat()

        unstructured_data_server_id: str | Unset = UNSET
        if not isinstance(self.unstructured_data_server_id, Unset):
            unstructured_data_server_id = str(self.unstructured_data_server_id)

        path = self.path

        copy_to_backup_server = self.copy_to_backup_server

        restore_permissions = self.restore_permissions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourcePath": source_path,
                "restoreMode": restore_mode,
            }
        )
        if is_recursive is not UNSET:
            field_dict["isRecursive"] = is_recursive
        if to_date_time is not UNSET:
            field_dict["toDateTime"] = to_date_time
        if unstructured_data_server_id is not UNSET:
            field_dict["unstructuredDataServerId"] = unstructured_data_server_id
        if path is not UNSET:
            field_dict["path"] = path
        if copy_to_backup_server is not UNSET:
            field_dict["copyToBackupServer"] = copy_to_backup_server
        if restore_permissions is not UNSET:
            field_dict["restorePermissions"] = restore_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_path = cast(list[str], d.pop("sourcePath"))

        restore_mode = EFileBackupFLRCopyToRestoreMode(d.pop("restoreMode"))

        is_recursive = d.pop("isRecursive", UNSET)

        _to_date_time = d.pop("toDateTime", UNSET)
        to_date_time: datetime.datetime | Unset
        if isinstance(_to_date_time, Unset):
            to_date_time = UNSET
        else:
            to_date_time = isoparse(_to_date_time)

        _unstructured_data_server_id = d.pop("unstructuredDataServerId", UNSET)
        unstructured_data_server_id: UUID | Unset
        if isinstance(_unstructured_data_server_id, Unset):
            unstructured_data_server_id = UNSET
        else:
            unstructured_data_server_id = UUID(_unstructured_data_server_id)

        path = d.pop("path", UNSET)

        copy_to_backup_server = d.pop("copyToBackupServer", UNSET)

        restore_permissions = d.pop("restorePermissions", UNSET)

        file_backup_flr_copy_to_spec = cls(
            source_path=source_path,
            restore_mode=restore_mode,
            is_recursive=is_recursive,
            to_date_time=to_date_time,
            unstructured_data_server_id=unstructured_data_server_id,
            path=path,
            copy_to_backup_server=copy_to_backup_server,
            restore_permissions=restore_permissions,
        )

        file_backup_flr_copy_to_spec.additional_properties = d
        return file_backup_flr_copy_to_spec

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
