from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_session_state import ESessionState
from ..models.e_session_type import ESessionType
from ..models.e_task_session_algorithm import ETaskSessionAlgorithm
from ..models.e_task_session_type import ETaskSessionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_progress_type_0 import SessionProgressType0
    from ..models.session_result_model import SessionResultModel


T = TypeVar("T", bound="BackupTaskSessionModel")


@_attrs_define
class BackupTaskSessionModel:
    """Backup task session.

    Attributes:
        id (UUID): Task session ID.
        type_ (ETaskSessionType): Task session type.
        session_id (UUID): Session ID.
        session_type (ESessionType): Type of the session.
        creation_time (datetime.datetime): Date and time when the task session was created.
        name (str): Name of the object.
        usn (int): Update sequence number.
        state (ESessionState): State of the session.
        end_time (datetime.datetime | Unset): Date and time when the task session ended.
        restore_point_id (UUID | Unset): Restore point ID.
        restore_point_reference (str | Unset): Restore point reference in the `/api/v1/restorePoints/{restorePointId}`
            format.
        algorithm (ETaskSessionAlgorithm | Unset): Task session algorithm type.
        repository_id (UUID | Unset): Repository ID.
        result (SessionResultModel | Unset): Session result.
        progress (None | SessionProgressType0 | Unset): Details on the progress of the session.
    """

    id: UUID
    type_: ETaskSessionType
    session_id: UUID
    session_type: ESessionType
    creation_time: datetime.datetime
    name: str
    usn: int
    state: ESessionState
    end_time: datetime.datetime | Unset = UNSET
    restore_point_id: UUID | Unset = UNSET
    restore_point_reference: str | Unset = UNSET
    algorithm: ETaskSessionAlgorithm | Unset = UNSET
    repository_id: UUID | Unset = UNSET
    result: SessionResultModel | Unset = UNSET
    progress: None | SessionProgressType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.session_progress_type_0 import SessionProgressType0

        id = str(self.id)

        type_ = self.type_.value

        session_id = str(self.session_id)

        session_type = self.session_type.value

        creation_time = self.creation_time.isoformat()

        name = self.name

        usn = self.usn

        state = self.state.value

        end_time: str | Unset = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        restore_point_reference = self.restore_point_reference

        algorithm: str | Unset = UNSET
        if not isinstance(self.algorithm, Unset):
            algorithm = self.algorithm.value

        repository_id: str | Unset = UNSET
        if not isinstance(self.repository_id, Unset):
            repository_id = str(self.repository_id)

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        progress: dict[str, Any] | None | Unset
        if isinstance(self.progress, Unset):
            progress = UNSET
        elif isinstance(self.progress, SessionProgressType0):
            progress = self.progress.to_dict()
        else:
            progress = self.progress

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
                "usn": usn,
                "state": state,
            }
        )
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id
        if restore_point_reference is not UNSET:
            field_dict["restorePointReference"] = restore_point_reference
        if algorithm is not UNSET:
            field_dict["algorithm"] = algorithm
        if repository_id is not UNSET:
            field_dict["repositoryId"] = repository_id
        if result is not UNSET:
            field_dict["result"] = result
        if progress is not UNSET:
            field_dict["progress"] = progress

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_progress_type_0 import SessionProgressType0
        from ..models.session_result_model import SessionResultModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ETaskSessionType(d.pop("type"))

        session_id = UUID(d.pop("sessionId"))

        session_type = ESessionType(d.pop("sessionType"))

        creation_time = isoparse(d.pop("creationTime"))

        name = d.pop("name")

        usn = d.pop("usn")

        state = ESessionState(d.pop("state"))

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

        _algorithm = d.pop("algorithm", UNSET)
        algorithm: ETaskSessionAlgorithm | Unset
        if isinstance(_algorithm, Unset):
            algorithm = UNSET
        else:
            algorithm = ETaskSessionAlgorithm(_algorithm)

        _repository_id = d.pop("repositoryId", UNSET)
        repository_id: UUID | Unset
        if isinstance(_repository_id, Unset):
            repository_id = UNSET
        else:
            repository_id = UUID(_repository_id)

        _result = d.pop("result", UNSET)
        result: SessionResultModel | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = SessionResultModel.from_dict(_result)

        def _parse_progress(data: object) -> None | SessionProgressType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_session_progress_type_0 = SessionProgressType0.from_dict(data)

                return componentsschemas_session_progress_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SessionProgressType0 | Unset, data)

        progress = _parse_progress(d.pop("progress", UNSET))

        backup_task_session_model = cls(
            id=id,
            type_=type_,
            session_id=session_id,
            session_type=session_type,
            creation_time=creation_time,
            name=name,
            usn=usn,
            state=state,
            end_time=end_time,
            restore_point_id=restore_point_id,
            restore_point_reference=restore_point_reference,
            algorithm=algorithm,
            repository_id=repository_id,
            result=result,
            progress=progress,
        )

        backup_task_session_model.additional_properties = d
        return backup_task_session_model

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
