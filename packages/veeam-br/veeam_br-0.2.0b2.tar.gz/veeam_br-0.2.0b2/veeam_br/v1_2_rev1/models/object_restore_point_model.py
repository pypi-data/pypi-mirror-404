from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_object_restore_point_operation import EObjectRestorePointOperation
from ..models.e_platform_type import EPlatformType
from ..models.e_restore_point_type import ERestorePointType
from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectRestorePointModel")


@_attrs_define
class ObjectRestorePointModel:
    """
    Attributes:
        id (UUID): ID of the restore point.
        name (str): Object name.
        platform_name (EPlatformType): Platform type.
        platform_id (UUID): ID of a platform where the object was created.
        creation_time (datetime.datetime): Date and time when the restore point was created.
        backup_id (UUID): ID of a backup that contains the restore point.
        allowed_operations (list[EObjectRestorePointOperation]): Array of operations allowed for the restore point.
        type_ (ERestorePointType | Unset): Restore point type.
        session_id (UUID | Unset): Session ID.
        malware_status (ESuspiciousActivitySeverity | Unset): Malware status.
        backup_file_id (UUID | Unset): Id of a file this restore point is stored in.
    """

    id: UUID
    name: str
    platform_name: EPlatformType
    platform_id: UUID
    creation_time: datetime.datetime
    backup_id: UUID
    allowed_operations: list[EObjectRestorePointOperation]
    type_: ERestorePointType | Unset = UNSET
    session_id: UUID | Unset = UNSET
    malware_status: ESuspiciousActivitySeverity | Unset = UNSET
    backup_file_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        platform_name = self.platform_name.value

        platform_id = str(self.platform_id)

        creation_time = self.creation_time.isoformat()

        backup_id = str(self.backup_id)

        allowed_operations = []
        for allowed_operations_item_data in self.allowed_operations:
            allowed_operations_item = allowed_operations_item_data.value
            allowed_operations.append(allowed_operations_item)

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        malware_status: str | Unset = UNSET
        if not isinstance(self.malware_status, Unset):
            malware_status = self.malware_status.value

        backup_file_id: str | Unset = UNSET
        if not isinstance(self.backup_file_id, Unset):
            backup_file_id = str(self.backup_file_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "platformName": platform_name,
                "platformId": platform_id,
                "creationTime": creation_time,
                "backupId": backup_id,
                "allowedOperations": allowed_operations,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if session_id is not UNSET:
            field_dict["sessionId"] = session_id
        if malware_status is not UNSET:
            field_dict["malwareStatus"] = malware_status
        if backup_file_id is not UNSET:
            field_dict["backupFileId"] = backup_file_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        platform_name = EPlatformType(d.pop("platformName"))

        platform_id = UUID(d.pop("platformId"))

        creation_time = isoparse(d.pop("creationTime"))

        backup_id = UUID(d.pop("backupId"))

        allowed_operations = []
        _allowed_operations = d.pop("allowedOperations")
        for allowed_operations_item_data in _allowed_operations:
            allowed_operations_item = EObjectRestorePointOperation(allowed_operations_item_data)

            allowed_operations.append(allowed_operations_item)

        _type_ = d.pop("type", UNSET)
        type_: ERestorePointType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ERestorePointType(_type_)

        _session_id = d.pop("sessionId", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        _malware_status = d.pop("malwareStatus", UNSET)
        malware_status: ESuspiciousActivitySeverity | Unset
        if isinstance(_malware_status, Unset):
            malware_status = UNSET
        else:
            malware_status = ESuspiciousActivitySeverity(_malware_status)

        _backup_file_id = d.pop("backupFileId", UNSET)
        backup_file_id: UUID | Unset
        if isinstance(_backup_file_id, Unset):
            backup_file_id = UNSET
        else:
            backup_file_id = UUID(_backup_file_id)

        object_restore_point_model = cls(
            id=id,
            name=name,
            platform_name=platform_name,
            platform_id=platform_id,
            creation_time=creation_time,
            backup_id=backup_id,
            allowed_operations=allowed_operations,
            type_=type_,
            session_id=session_id,
            malware_status=malware_status,
            backup_file_id=backup_file_id,
        )

        object_restore_point_model.additional_properties = d
        return object_restore_point_model

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
