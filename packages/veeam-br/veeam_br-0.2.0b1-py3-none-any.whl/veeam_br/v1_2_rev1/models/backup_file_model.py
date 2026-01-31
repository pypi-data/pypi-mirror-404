from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_backup_file_gfs_period import EBackupFileGFSPeriod
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupFileModel")


@_attrs_define
class BackupFileModel:
    """
    Attributes:
        id (UUID): Backup file ID.
        name (str): Path of the backup file.
        backup_id (UUID): Backup ID.
        object_id (UUID): Object ID.
        data_size (int): Amount of data in bytes, before compression and deduplication.
        backup_size (int): Actual, physical amount of data in bytes, stored in the repository after compression and
            deduplication.
        dedup_ratio (int): Deduplication ratio of the backup file.
        compress_ratio (int): Compression ratio of the backup file.
        creation_time (datetime.datetime): Date and time the backup file was created.
        restore_point_ids (list[UUID] | Unset): Array of IDs of the restore points associated with the backup file.
        gfs_periods (list[EBackupFileGFSPeriod] | Unset): Array of GFS flags assigned to the backup file.
    """

    id: UUID
    name: str
    backup_id: UUID
    object_id: UUID
    data_size: int
    backup_size: int
    dedup_ratio: int
    compress_ratio: int
    creation_time: datetime.datetime
    restore_point_ids: list[UUID] | Unset = UNSET
    gfs_periods: list[EBackupFileGFSPeriod] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        backup_id = str(self.backup_id)

        object_id = str(self.object_id)

        data_size = self.data_size

        backup_size = self.backup_size

        dedup_ratio = self.dedup_ratio

        compress_ratio = self.compress_ratio

        creation_time = self.creation_time.isoformat()

        restore_point_ids: list[str] | Unset = UNSET
        if not isinstance(self.restore_point_ids, Unset):
            restore_point_ids = []
            for restore_point_ids_item_data in self.restore_point_ids:
                restore_point_ids_item = str(restore_point_ids_item_data)
                restore_point_ids.append(restore_point_ids_item)

        gfs_periods: list[str] | Unset = UNSET
        if not isinstance(self.gfs_periods, Unset):
            gfs_periods = []
            for gfs_periods_item_data in self.gfs_periods:
                gfs_periods_item = gfs_periods_item_data.value
                gfs_periods.append(gfs_periods_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "backupId": backup_id,
                "objectId": object_id,
                "dataSize": data_size,
                "backupSize": backup_size,
                "dedupRatio": dedup_ratio,
                "compressRatio": compress_ratio,
                "creationTime": creation_time,
            }
        )
        if restore_point_ids is not UNSET:
            field_dict["restorePointIds"] = restore_point_ids
        if gfs_periods is not UNSET:
            field_dict["gfsPeriods"] = gfs_periods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        backup_id = UUID(d.pop("backupId"))

        object_id = UUID(d.pop("objectId"))

        data_size = d.pop("dataSize")

        backup_size = d.pop("backupSize")

        dedup_ratio = d.pop("dedupRatio")

        compress_ratio = d.pop("compressRatio")

        creation_time = isoparse(d.pop("creationTime"))

        _restore_point_ids = d.pop("restorePointIds", UNSET)
        restore_point_ids: list[UUID] | Unset = UNSET
        if _restore_point_ids is not UNSET:
            restore_point_ids = []
            for restore_point_ids_item_data in _restore_point_ids:
                restore_point_ids_item = UUID(restore_point_ids_item_data)

                restore_point_ids.append(restore_point_ids_item)

        _gfs_periods = d.pop("gfsPeriods", UNSET)
        gfs_periods: list[EBackupFileGFSPeriod] | Unset = UNSET
        if _gfs_periods is not UNSET:
            gfs_periods = []
            for gfs_periods_item_data in _gfs_periods:
                gfs_periods_item = EBackupFileGFSPeriod(gfs_periods_item_data)

                gfs_periods.append(gfs_periods_item)

        backup_file_model = cls(
            id=id,
            name=name,
            backup_id=backup_id,
            object_id=object_id,
            data_size=data_size,
            backup_size=backup_size,
            dedup_ratio=dedup_ratio,
            compress_ratio=compress_ratio,
            creation_time=creation_time,
            restore_point_ids=restore_point_ids,
            gfs_periods=gfs_periods,
        )

        backup_file_model.additional_properties = d
        return backup_file_model

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
