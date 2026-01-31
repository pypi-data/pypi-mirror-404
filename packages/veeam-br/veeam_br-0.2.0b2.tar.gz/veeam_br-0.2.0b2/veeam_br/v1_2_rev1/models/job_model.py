from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType

T = TypeVar("T", bound="JobModel")


@_attrs_define
class JobModel:
    """
    Attributes:
        id (UUID): ID of the job.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        is_disabled (bool): If `true`, the job is disabled.
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "isDisabled": is_disabled,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        job_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
        )

        job_model.additional_properties = d
        return job_model

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
