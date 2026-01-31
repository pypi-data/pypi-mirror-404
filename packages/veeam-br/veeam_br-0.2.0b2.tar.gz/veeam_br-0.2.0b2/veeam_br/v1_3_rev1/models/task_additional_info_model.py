from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TaskAdditionalInfoModel")


@_attrs_define
class TaskAdditionalInfoModel:
    """Task details.

    Attributes:
        message (str): Message that explains the task result.
        resource_id (UUID | Unset): ID of the resource.
        resource_reference (str | Unset): URI of the resource.
    """

    message: str
    resource_id: UUID | Unset = UNSET
    resource_reference: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        resource_id: str | Unset = UNSET
        if not isinstance(self.resource_id, Unset):
            resource_id = str(self.resource_id)

        resource_reference = self.resource_reference

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
            }
        )
        if resource_id is not UNSET:
            field_dict["resourceId"] = resource_id
        if resource_reference is not UNSET:
            field_dict["resourceReference"] = resource_reference

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        _resource_id = d.pop("resourceId", UNSET)
        resource_id: UUID | Unset
        if isinstance(_resource_id, Unset):
            resource_id = UNSET
        else:
            resource_id = UUID(_resource_id)

        resource_reference = d.pop("resourceReference", UNSET)

        task_additional_info_model = cls(
            message=message,
            resource_id=resource_id,
            resource_reference=resource_reference,
        )

        task_additional_info_model.additional_properties = d
        return task_additional_info_model

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
