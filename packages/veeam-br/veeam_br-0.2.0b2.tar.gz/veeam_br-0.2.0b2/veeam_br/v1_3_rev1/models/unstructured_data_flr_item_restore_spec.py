from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_unstructured_data_flr_restore_mode import EUnstructuredDataFLRRestoreMode
from ..models.e_unstructured_data_flr_restore_type import EUnstructuredDataFLRRestoreType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataFLRItemRestoreSpec")


@_attrs_define
class UnstructuredDataFLRItemRestoreSpec:
    """Settings for restoring guest OS items from unstructured data share.

    Attributes:
        source_path (list[str]): Array of paths to the items that you want to restore.
        restore_type (EUnstructuredDataFLRRestoreType): Restore type.
        is_recursive (bool | Unset): If `true`, all files and folders in the source path are restored recursively.
        restore_mode (EUnstructuredDataFLRRestoreMode | Unset): Restore point settings.<p> Use this property if you have
            specified the `unstructuredDataServerId` and the `backupId` properties in the [Start File Restore from
            Unstructured Data Backup](Restore#operation/StartUnstructuredDataFlrMount) request that you used to mount the
            share. In this case, you provide information about the restore point in this property.<p> Do not use this
            property if you have specified the `restorePointId` property in the [Start File Restore from Unstructured Data
            Backup](Restore#operation/StartUnstructuredDataFlrMount) request. In this case, Veeam Backup & Replication uses
            the restore point whose ID you specified.
        to_date_time (datetime.datetime | Unset): Date when the restore point was created. Use this property when
            restoring files and folders from an earlier restore point (the `restoreMode` value is `Custom`).
        restore_permissions (bool | Unset): If `true`, Veeam Backup & Replication will restore permissions and security
            attributes of the backups.
    """

    source_path: list[str]
    restore_type: EUnstructuredDataFLRRestoreType
    is_recursive: bool | Unset = UNSET
    restore_mode: EUnstructuredDataFLRRestoreMode | Unset = UNSET
    to_date_time: datetime.datetime | Unset = UNSET
    restore_permissions: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_path = self.source_path

        restore_type = self.restore_type.value

        is_recursive = self.is_recursive

        restore_mode: str | Unset = UNSET
        if not isinstance(self.restore_mode, Unset):
            restore_mode = self.restore_mode.value

        to_date_time: str | Unset = UNSET
        if not isinstance(self.to_date_time, Unset):
            to_date_time = self.to_date_time.isoformat()

        restore_permissions = self.restore_permissions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourcePath": source_path,
                "restoreType": restore_type,
            }
        )
        if is_recursive is not UNSET:
            field_dict["isRecursive"] = is_recursive
        if restore_mode is not UNSET:
            field_dict["restoreMode"] = restore_mode
        if to_date_time is not UNSET:
            field_dict["toDateTime"] = to_date_time
        if restore_permissions is not UNSET:
            field_dict["restorePermissions"] = restore_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_path = cast(list[str], d.pop("sourcePath"))

        restore_type = EUnstructuredDataFLRRestoreType(d.pop("restoreType"))

        is_recursive = d.pop("isRecursive", UNSET)

        _restore_mode = d.pop("restoreMode", UNSET)
        restore_mode: EUnstructuredDataFLRRestoreMode | Unset
        if isinstance(_restore_mode, Unset):
            restore_mode = UNSET
        else:
            restore_mode = EUnstructuredDataFLRRestoreMode(_restore_mode)

        _to_date_time = d.pop("toDateTime", UNSET)
        to_date_time: datetime.datetime | Unset
        if isinstance(_to_date_time, Unset):
            to_date_time = UNSET
        else:
            to_date_time = isoparse(_to_date_time)

        restore_permissions = d.pop("restorePermissions", UNSET)

        unstructured_data_flr_item_restore_spec = cls(
            source_path=source_path,
            restore_type=restore_type,
            is_recursive=is_recursive,
            restore_mode=restore_mode,
            to_date_time=to_date_time,
            restore_permissions=restore_permissions,
        )

        unstructured_data_flr_item_restore_spec.additional_properties = d
        return unstructured_data_flr_item_restore_spec

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
