from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_extent_status_type import ERepositoryExtentStatusType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PerformanceExtentModel")


@_attrs_define
class PerformanceExtentModel:
    """
    Attributes:
        id (UUID): ID of the backup repository added as a performance extent.
        name (str): Name of the backup repository added as a performance extent.
        status (ERepositoryExtentStatusType | Unset): Performance extent status.
    """

    id: UUID
    name: str
    status: ERepositoryExtentStatusType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        _status = d.pop("status", UNSET)
        status: ERepositoryExtentStatusType | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ERepositoryExtentStatusType(_status)

        performance_extent_model = cls(
            id=id,
            name=name,
            status=status,
        )

        performance_extent_model.additional_properties = d
        return performance_extent_model

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
