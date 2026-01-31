from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_platform_type import EPlatformType
from ..models.e_session_state import ESessionState
from ..models.e_session_type import ESessionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_result_model import SessionResultModel


T = TypeVar("T", bound="SessionModel")


@_attrs_define
class SessionModel:
    """Session settings.

    Attributes:
        id (UUID): ID of the session.
        name (str): Name of the session.
        job_id (UUID): ID of the job or job related activity.
        session_type (ESessionType): Type of the session.
        creation_time (datetime.datetime): Date and time when the session was created.
        state (ESessionState): State of the session.
        usn (int): Update sequence number.
        end_time (datetime.datetime | Unset): Date and time when the session was ended.
        progress_percent (int | Unset): Progress percentage of the session.
        result (SessionResultModel | Unset): Session result.
        resource_id (UUID | Unset): ID of the resource.
        resource_reference (str | Unset): URI of the resource.
        parent_session_id (UUID | Unset): ID of the parent session.
        platform_name (EPlatformType | Unset): Platform type.
        platform_id (UUID | Unset): ID of the resource platform. The value is always
            *00000000-0000-0000-0000-000000000000* except for custom platforms.
        initiated_by (str | Unset): Name of the user that initiated the session.
    """

    id: UUID
    name: str
    job_id: UUID
    session_type: ESessionType
    creation_time: datetime.datetime
    state: ESessionState
    usn: int
    end_time: datetime.datetime | Unset = UNSET
    progress_percent: int | Unset = UNSET
    result: SessionResultModel | Unset = UNSET
    resource_id: UUID | Unset = UNSET
    resource_reference: str | Unset = UNSET
    parent_session_id: UUID | Unset = UNSET
    platform_name: EPlatformType | Unset = UNSET
    platform_id: UUID | Unset = UNSET
    initiated_by: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        job_id = str(self.job_id)

        session_type = self.session_type.value

        creation_time = self.creation_time.isoformat()

        state = self.state.value

        usn = self.usn

        end_time: str | Unset = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()

        progress_percent = self.progress_percent

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        resource_id: str | Unset = UNSET
        if not isinstance(self.resource_id, Unset):
            resource_id = str(self.resource_id)

        resource_reference = self.resource_reference

        parent_session_id: str | Unset = UNSET
        if not isinstance(self.parent_session_id, Unset):
            parent_session_id = str(self.parent_session_id)

        platform_name: str | Unset = UNSET
        if not isinstance(self.platform_name, Unset):
            platform_name = self.platform_name.value

        platform_id: str | Unset = UNSET
        if not isinstance(self.platform_id, Unset):
            platform_id = str(self.platform_id)

        initiated_by = self.initiated_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "jobId": job_id,
                "sessionType": session_type,
                "creationTime": creation_time,
                "state": state,
                "usn": usn,
            }
        )
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if progress_percent is not UNSET:
            field_dict["progressPercent"] = progress_percent
        if result is not UNSET:
            field_dict["result"] = result
        if resource_id is not UNSET:
            field_dict["resourceId"] = resource_id
        if resource_reference is not UNSET:
            field_dict["resourceReference"] = resource_reference
        if parent_session_id is not UNSET:
            field_dict["parentSessionId"] = parent_session_id
        if platform_name is not UNSET:
            field_dict["platformName"] = platform_name
        if platform_id is not UNSET:
            field_dict["platformId"] = platform_id
        if initiated_by is not UNSET:
            field_dict["initiatedBy"] = initiated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_result_model import SessionResultModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        job_id = UUID(d.pop("jobId"))

        session_type = ESessionType(d.pop("sessionType"))

        creation_time = isoparse(d.pop("creationTime"))

        state = ESessionState(d.pop("state"))

        usn = d.pop("usn")

        _end_time = d.pop("endTime", UNSET)
        end_time: datetime.datetime | Unset
        if isinstance(_end_time, Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)

        progress_percent = d.pop("progressPercent", UNSET)

        _result = d.pop("result", UNSET)
        result: SessionResultModel | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = SessionResultModel.from_dict(_result)

        _resource_id = d.pop("resourceId", UNSET)
        resource_id: UUID | Unset
        if isinstance(_resource_id, Unset):
            resource_id = UNSET
        else:
            resource_id = UUID(_resource_id)

        resource_reference = d.pop("resourceReference", UNSET)

        _parent_session_id = d.pop("parentSessionId", UNSET)
        parent_session_id: UUID | Unset
        if isinstance(_parent_session_id, Unset):
            parent_session_id = UNSET
        else:
            parent_session_id = UUID(_parent_session_id)

        _platform_name = d.pop("platformName", UNSET)
        platform_name: EPlatformType | Unset
        if isinstance(_platform_name, Unset):
            platform_name = UNSET
        else:
            platform_name = EPlatformType(_platform_name)

        _platform_id = d.pop("platformId", UNSET)
        platform_id: UUID | Unset
        if isinstance(_platform_id, Unset):
            platform_id = UNSET
        else:
            platform_id = UUID(_platform_id)

        initiated_by = d.pop("initiatedBy", UNSET)

        session_model = cls(
            id=id,
            name=name,
            job_id=job_id,
            session_type=session_type,
            creation_time=creation_time,
            state=state,
            usn=usn,
            end_time=end_time,
            progress_percent=progress_percent,
            result=result,
            resource_id=resource_id,
            resource_reference=resource_reference,
            parent_session_id=parent_session_id,
            platform_name=platform_name,
            platform_id=platform_id,
            initiated_by=initiated_by,
        )

        session_model.additional_properties = d
        return session_model

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
