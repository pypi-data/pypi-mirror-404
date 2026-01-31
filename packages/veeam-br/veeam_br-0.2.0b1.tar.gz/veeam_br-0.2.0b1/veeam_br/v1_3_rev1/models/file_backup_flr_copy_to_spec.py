from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_unstructured_data_flr_restore_mode import EUnstructuredDataFLRRestoreMode
from ..models.e_unstructured_data_flr_restore_type import EUnstructuredDataFLRRestoreType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FileBackupFLRCopyToSpec")


@_attrs_define
class FileBackupFLRCopyToSpec:
    """Settings for copying file system items.

    Attributes:
        source_path (list[str]): Array of paths to the items that you want to restore.
        is_recursive (bool | Unset): If `true`, all files and folders in the source path are copied recursively.
        restore_mode (EUnstructuredDataFLRRestoreMode | Unset): Restore point settings.<p> Use this property if you have
            specified the `unstructuredDataServerId` and the `backupId` properties in the [Start File Restore from
            Unstructured Data Backup](Restore#operation/StartUnstructuredDataFlrMount) request that you used to mount the
            share. In this case, you provide information about the restore point in this property.<p> Do not use this
            property if you have specified the `restorePointId` property in the [Start File Restore from Unstructured Data
            Backup](Restore#operation/StartUnstructuredDataFlrMount) request. In this case, Veeam Backup & Replication uses
            the restore point whose ID you specified.
        restore_type (EUnstructuredDataFLRRestoreType | Unset): Restore type.
        to_date_time (datetime.datetime | Unset): Date when the restore point was created. Use this property when
            copying files and folders from an earlier restore point (the `restoreMode` value is `Custom`).
        unstructured_data_server_id (UUID | Unset): ID of a server where the target shared folder is located. Use this
            property when copying files and folders to a file share. To get the ID, run the [Get All Unstructured Data
            Servers](Inventory-Browser#operation/GetAllUnstructuredDataServers) request.
        path (str | Unset): Path to the target folder.
        copy_to_backup_server (bool | Unset): If `true`, the files and folders are copied to a folder on the machine
            where the Veeam Backup & Replication console is installed.
        restore_permissions (bool | Unset): If `true`, Veeam Backup & Replication will restore permissions and security
            attributes of the backups.
    """

    source_path: list[str]
    is_recursive: bool | Unset = UNSET
    restore_mode: EUnstructuredDataFLRRestoreMode | Unset = UNSET
    restore_type: EUnstructuredDataFLRRestoreType | Unset = UNSET
    to_date_time: datetime.datetime | Unset = UNSET
    unstructured_data_server_id: UUID | Unset = UNSET
    path: str | Unset = UNSET
    copy_to_backup_server: bool | Unset = UNSET
    restore_permissions: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_path = self.source_path

        is_recursive = self.is_recursive

        restore_mode: str | Unset = UNSET
        if not isinstance(self.restore_mode, Unset):
            restore_mode = self.restore_mode.value

        restore_type: str | Unset = UNSET
        if not isinstance(self.restore_type, Unset):
            restore_type = self.restore_type.value

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
            }
        )
        if is_recursive is not UNSET:
            field_dict["isRecursive"] = is_recursive
        if restore_mode is not UNSET:
            field_dict["restoreMode"] = restore_mode
        if restore_type is not UNSET:
            field_dict["restoreType"] = restore_type
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

        is_recursive = d.pop("isRecursive", UNSET)

        _restore_mode = d.pop("restoreMode", UNSET)
        restore_mode: EUnstructuredDataFLRRestoreMode | Unset
        if isinstance(_restore_mode, Unset):
            restore_mode = UNSET
        else:
            restore_mode = EUnstructuredDataFLRRestoreMode(_restore_mode)

        _restore_type = d.pop("restoreType", UNSET)
        restore_type: EUnstructuredDataFLRRestoreType | Unset
        if isinstance(_restore_type, Unset):
            restore_type = UNSET
        else:
            restore_type = EUnstructuredDataFLRRestoreType(_restore_type)

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
            is_recursive=is_recursive,
            restore_mode=restore_mode,
            restore_type=restore_type,
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
