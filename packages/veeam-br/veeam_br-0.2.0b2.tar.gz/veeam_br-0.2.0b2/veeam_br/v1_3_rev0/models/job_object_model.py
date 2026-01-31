from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobObjectModel")


@_attrs_define
class JobObjectModel:
    """Job object.

    Attributes:
        id (UUID): Job ID.
        name (str | Unset): Name of the job.
        type_ (EJobType | Unset): Type of the job.
    """

    id: UUID
    name: str | Unset = UNSET
    type_: EJobType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: EJobType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EJobType(_type_)

        job_object_model = cls(
            id=id,
            name=name,
            type_=type_,
        )

        job_object_model.additional_properties = d
        return job_object_model

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
