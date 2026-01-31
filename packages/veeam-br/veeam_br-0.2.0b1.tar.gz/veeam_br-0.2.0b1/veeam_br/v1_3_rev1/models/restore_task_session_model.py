from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_session_state import ESessionState
from ..models.e_session_type import ESessionType
from ..models.e_task_session_type import ETaskSessionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_result_model import SessionResultModel


T = TypeVar("T", bound="RestoreTaskSessionModel")


@_attrs_define
class RestoreTaskSessionModel:
    """Settings of restore task session.

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
        result (SessionResultModel | Unset): Session result.
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
    result: SessionResultModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

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
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        _result = d.pop("result", UNSET)
        result: SessionResultModel | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = SessionResultModel.from_dict(_result)

        restore_task_session_model = cls(
            id=id,
            type_=type_,
            session_id=session_id,
            session_type=session_type,
            creation_time=creation_time,
            name=name,
            usn=usn,
            state=state,
            end_time=end_time,
            result=result,
        )

        restore_task_session_model.additional_properties = d
        return restore_task_session_model

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
