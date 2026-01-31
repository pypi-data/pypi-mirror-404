from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UserRolePermissionsModel")


@_attrs_define
class UserRolePermissionsModel:
    """Role permissions.

    Attributes:
        role_id (UUID): Role ID.
        permissions (list[str]): Array of role permissions.
    """

    role_id: UUID
    permissions: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role_id = str(self.role_id)

        permissions = self.permissions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "roleId": role_id,
                "permissions": permissions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        role_id = UUID(d.pop("roleId"))

        permissions = cast(list[str], d.pop("permissions"))

        user_role_permissions_model = cls(
            role_id=role_id,
            permissions=permissions,
        )

        user_role_permissions_model.additional_properties = d
        return user_role_permissions_model

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
