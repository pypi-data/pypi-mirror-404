from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_task_result import ETaskResult
from ..models.e_task_state import ETaskState
from ..models.e_task_type import ETaskType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_additional_info_model import TaskAdditionalInfoModel


T = TypeVar("T", bound="FlrDownloadTaskModel")


@_attrs_define
class FlrDownloadTaskModel:
    """File restore download task.

    Attributes:
        id (UUID): ID of the task.
        type_ (ETaskType): Task type.
        name (str): Task name.
        state (ETaskState): Task state.
        progress_percent (int): Progress percentage of the task.
        creation_time (datetime.datetime): Date and time when the task was created.
        result (ETaskResult): Task result.
        end_time (datetime.datetime | Unset): Date and time when the task was ended.
        additional_info (TaskAdditionalInfoModel | Unset): Task details.
    """

    id: UUID
    type_: ETaskType
    name: str
    state: ETaskState
    progress_percent: int
    creation_time: datetime.datetime
    result: ETaskResult
    end_time: datetime.datetime | Unset = UNSET
    additional_info: TaskAdditionalInfoModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        name = self.name

        state = self.state.value

        progress_percent = self.progress_percent

        creation_time = self.creation_time.isoformat()

        result = self.result.value

        end_time: str | Unset = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()

        additional_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.additional_info, Unset):
            additional_info = self.additional_info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "name": name,
                "state": state,
                "progressPercent": progress_percent,
                "creationTime": creation_time,
                "result": result,
            }
        )
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if additional_info is not UNSET:
            field_dict["additionalInfo"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_additional_info_model import TaskAdditionalInfoModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ETaskType(d.pop("type"))

        name = d.pop("name")

        state = ETaskState(d.pop("state"))

        progress_percent = d.pop("progressPercent")

        creation_time = isoparse(d.pop("creationTime"))

        result = ETaskResult(d.pop("result"))

        _end_time = d.pop("endTime", UNSET)
        end_time: datetime.datetime | Unset
        if isinstance(_end_time, Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)

        _additional_info = d.pop("additionalInfo", UNSET)
        additional_info: TaskAdditionalInfoModel | Unset
        if isinstance(_additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = TaskAdditionalInfoModel.from_dict(_additional_info)

        flr_download_task_model = cls(
            id=id,
            type_=type_,
            name=name,
            state=state,
            progress_percent=progress_percent,
            creation_time=creation_time,
            result=result,
            end_time=end_time,
            additional_info=additional_info,
        )

        flr_download_task_model.additional_properties = d
        return flr_download_task_model

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
