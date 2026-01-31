from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_platform_type import EPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupObjectModel")


@_attrs_define
class BackupObjectModel:
    """
    Attributes:
        id (UUID): ID of the object.
        platform_name (EPlatformType): Platform type.
        name (str | Unset): Name of the object.
        type_ (str | Unset): Type of the object.
        platform_id (UUID | Unset): ID of the platform where the object was created. The value is always
            *00000000-0000-0000-0000-000000000000* except for custom platforms.
        restore_points_count (int | Unset): Number of restore points.
    """

    id: UUID
    platform_name: EPlatformType
    name: str | Unset = UNSET
    type_: str | Unset = UNSET
    platform_id: UUID | Unset = UNSET
    restore_points_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        platform_name = self.platform_name.value

        name = self.name

        type_ = self.type_

        platform_id: str | Unset = UNSET
        if not isinstance(self.platform_id, Unset):
            platform_id = str(self.platform_id)

        restore_points_count = self.restore_points_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "platformName": platform_name,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if platform_id is not UNSET:
            field_dict["platformId"] = platform_id
        if restore_points_count is not UNSET:
            field_dict["restorePointsCount"] = restore_points_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        platform_name = EPlatformType(d.pop("platformName"))

        name = d.pop("name", UNSET)

        type_ = d.pop("type", UNSET)

        _platform_id = d.pop("platformId", UNSET)
        platform_id: UUID | Unset
        if isinstance(_platform_id, Unset):
            platform_id = UNSET
        else:
            platform_id = UUID(_platform_id)

        restore_points_count = d.pop("restorePointsCount", UNSET)

        backup_object_model = cls(
            id=id,
            platform_name=platform_name,
            name=name,
            type_=type_,
            platform_id=platform_id,
            restore_points_count=restore_points_count,
        )

        backup_object_model.additional_properties = d
        return backup_object_model

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
