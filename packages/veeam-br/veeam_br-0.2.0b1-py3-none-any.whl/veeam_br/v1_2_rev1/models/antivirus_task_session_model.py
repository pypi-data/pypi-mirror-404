from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_antivirus_scan_result import EAntivirusScanResult
from ..models.e_antivirus_scan_state import EAntivirusScanState
from ..models.e_antivirus_scan_type import EAntivirusScanType
from ..models.e_session_type import ESessionType
from ..models.e_task_session_type import ETaskSessionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AntivirusTaskSessionModel")


@_attrs_define
class AntivirusTaskSessionModel:
    """
    Attributes:
        id (UUID): Task session ID.
        type_ (ETaskSessionType): Task session type.
        session_id (UUID): Session ID.
        session_type (ESessionType): Type of the session.
        creation_time (datetime.datetime): Date and time when the task session was created.
        name (str): Name of the object.
        scan_type (EAntivirusScanType): Type of antivirus scan.
        scan_result (EAntivirusScanResult): Antivirus scan result.
        scan_state (EAntivirusScanState): State of the antivirus scan.
        end_time (datetime.datetime | Unset): Date and time when the task session ended.
        restore_point_id (UUID | Unset):
        restore_point_reference (str | Unset):
        antivirus_name (str | Unset):
    """

    id: UUID
    type_: ETaskSessionType
    session_id: UUID
    session_type: ESessionType
    creation_time: datetime.datetime
    name: str
    scan_type: EAntivirusScanType
    scan_result: EAntivirusScanResult
    scan_state: EAntivirusScanState
    end_time: datetime.datetime | Unset = UNSET
    restore_point_id: UUID | Unset = UNSET
    restore_point_reference: str | Unset = UNSET
    antivirus_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        session_id = str(self.session_id)

        session_type = self.session_type.value

        creation_time = self.creation_time.isoformat()

        name = self.name

        scan_type = self.scan_type.value

        scan_result = self.scan_result.value

        scan_state = self.scan_state.value

        end_time: str | Unset = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        restore_point_reference = self.restore_point_reference

        antivirus_name = self.antivirus_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "sessionId": session_id,
                "sessionType": session_type,
                "creationTime": creation_time,
                "name": name,
                "scanType": scan_type,
                "scanResult": scan_result,
                "scanState": scan_state,
            }
        )
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id
        if restore_point_reference is not UNSET:
            field_dict["restorePointReference"] = restore_point_reference
        if antivirus_name is not UNSET:
            field_dict["antivirusName"] = antivirus_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ETaskSessionType(d.pop("type"))

        session_id = UUID(d.pop("sessionId"))

        session_type = ESessionType(d.pop("sessionType"))

        creation_time = isoparse(d.pop("creationTime"))

        name = d.pop("name")

        scan_type = EAntivirusScanType(d.pop("scanType"))

        scan_result = EAntivirusScanResult(d.pop("scanResult"))

        scan_state = EAntivirusScanState(d.pop("scanState"))

        _end_time = d.pop("endTime", UNSET)
        end_time: datetime.datetime | Unset
        if isinstance(_end_time, Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)

        _restore_point_id = d.pop("restorePointId", UNSET)
        restore_point_id: UUID | Unset
        if isinstance(_restore_point_id, Unset):
            restore_point_id = UNSET
        else:
            restore_point_id = UUID(_restore_point_id)

        restore_point_reference = d.pop("restorePointReference", UNSET)

        antivirus_name = d.pop("antivirusName", UNSET)

        antivirus_task_session_model = cls(
            id=id,
            type_=type_,
            session_id=session_id,
            session_type=session_type,
            creation_time=creation_time,
            name=name,
            scan_type=scan_type,
            scan_result=scan_result,
            scan_state=scan_state,
            end_time=end_time,
            restore_point_id=restore_point_id,
            restore_point_reference=restore_point_reference,
            antivirus_name=antivirus_name,
        )

        antivirus_task_session_model.additional_properties = d
        return antivirus_task_session_model

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
