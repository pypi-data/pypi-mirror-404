from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_flr_item_restore_status import EFlrItemRestoreStatus
from ..models.e_flr_item_type import EFlrItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrTaskItemModel")


@_attrs_define
class FlrTaskItemModel:
    """Item restored in a file restore session.

    Attributes:
        item_type (EFlrItemType): Item type.
        source_path (str): Source path of the restored item.
        target_path (str): Target path for the restored item.
        target_host (str): Target server for the file restore operation.
        size (int): Item size, in bytes.
        restore_status (EFlrItemRestoreStatus): File restore status.
        job_name (str): Backup or replica job name.
        restore_start_time (datetime.datetime): Date and time when the restore session was started.
        restore_finish_time (datetime.datetime): Date and time when the restore session was finished.
        restore_session_id (UUID): Restore session ID.
        initiator_name (str): Account that initiated the restore session.
        name (str): Restored item name.
        restore_point_id (UUID | Unset): Restore point ID.
        restore_point_date (datetime.datetime | Unset): Date and time when the restore point was created.
    """

    item_type: EFlrItemType
    source_path: str
    target_path: str
    target_host: str
    size: int
    restore_status: EFlrItemRestoreStatus
    job_name: str
    restore_start_time: datetime.datetime
    restore_finish_time: datetime.datetime
    restore_session_id: UUID
    initiator_name: str
    name: str
    restore_point_id: UUID | Unset = UNSET
    restore_point_date: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_type = self.item_type.value

        source_path = self.source_path

        target_path = self.target_path

        target_host = self.target_host

        size = self.size

        restore_status = self.restore_status.value

        job_name = self.job_name

        restore_start_time = self.restore_start_time.isoformat()

        restore_finish_time = self.restore_finish_time.isoformat()

        restore_session_id = str(self.restore_session_id)

        initiator_name = self.initiator_name

        name = self.name

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        restore_point_date: str | Unset = UNSET
        if not isinstance(self.restore_point_date, Unset):
            restore_point_date = self.restore_point_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "itemType": item_type,
                "sourcePath": source_path,
                "targetPath": target_path,
                "targetHost": target_host,
                "size": size,
                "restoreStatus": restore_status,
                "jobName": job_name,
                "restoreStartTime": restore_start_time,
                "restoreFinishTime": restore_finish_time,
                "restoreSessionId": restore_session_id,
                "initiatorName": initiator_name,
                "name": name,
            }
        )
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id
        if restore_point_date is not UNSET:
            field_dict["restorePointDate"] = restore_point_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_type = EFlrItemType(d.pop("itemType"))

        source_path = d.pop("sourcePath")

        target_path = d.pop("targetPath")

        target_host = d.pop("targetHost")

        size = d.pop("size")

        restore_status = EFlrItemRestoreStatus(d.pop("restoreStatus"))

        job_name = d.pop("jobName")

        restore_start_time = isoparse(d.pop("restoreStartTime"))

        restore_finish_time = isoparse(d.pop("restoreFinishTime"))

        restore_session_id = UUID(d.pop("restoreSessionId"))

        initiator_name = d.pop("initiatorName")

        name = d.pop("name")

        _restore_point_id = d.pop("restorePointId", UNSET)
        restore_point_id: UUID | Unset
        if isinstance(_restore_point_id, Unset):
            restore_point_id = UNSET
        else:
            restore_point_id = UUID(_restore_point_id)

        _restore_point_date = d.pop("restorePointDate", UNSET)
        restore_point_date: datetime.datetime | Unset
        if isinstance(_restore_point_date, Unset):
            restore_point_date = UNSET
        else:
            restore_point_date = isoparse(_restore_point_date)

        flr_task_item_model = cls(
            item_type=item_type,
            source_path=source_path,
            target_path=target_path,
            target_host=target_host,
            size=size,
            restore_status=restore_status,
            job_name=job_name,
            restore_start_time=restore_start_time,
            restore_finish_time=restore_finish_time,
            restore_session_id=restore_session_id,
            initiator_name=initiator_name,
            name=name,
            restore_point_id=restore_point_id,
            restore_point_date=restore_point_date,
        )

        flr_task_item_model.additional_properties = d
        return flr_task_item_model

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
