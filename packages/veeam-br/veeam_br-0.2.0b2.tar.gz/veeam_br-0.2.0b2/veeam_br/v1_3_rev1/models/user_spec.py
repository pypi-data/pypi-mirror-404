from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_user_type import EUserType

if TYPE_CHECKING:
    from ..models.role_model import RoleModel


T = TypeVar("T", bound="UserSpec")


@_attrs_define
class UserSpec:
    """User settings.

    Attributes:
        name (str): User or group name.
        type_ (EUserType): User or group type.
        roles (list[RoleModel]): Array of roles assigned to the user or group.
        is_service_account (bool): If `true`, the user or group is a service account.
    """

    name: str
    type_: EUserType
    roles: list[RoleModel]
    is_service_account: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        roles = []
        for roles_item_data in self.roles:
            roles_item = roles_item_data.to_dict()
            roles.append(roles_item)

        is_service_account = self.is_service_account

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "roles": roles,
                "isServiceAccount": is_service_account,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.role_model import RoleModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EUserType(d.pop("type"))

        roles = []
        _roles = d.pop("roles")
        for roles_item_data in _roles:
            roles_item = RoleModel.from_dict(roles_item_data)

            roles.append(roles_item)

        is_service_account = d.pop("isServiceAccount")

        user_spec = cls(
            name=name,
            type_=type_,
            roles=roles,
            is_service_account=is_service_account,
        )

        user_spec.additional_properties = d
        return user_spec

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
