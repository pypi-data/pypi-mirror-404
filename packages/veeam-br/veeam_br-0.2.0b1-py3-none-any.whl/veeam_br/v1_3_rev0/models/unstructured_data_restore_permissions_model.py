from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_account_permission_type import EAccountPermissionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataRestorePermissionsModel")


@_attrs_define
class UnstructuredDataRestorePermissionsModel:
    r"""Permissions for restoring unstructured data.

    Attributes:
        owner (str): Name of the account or group in the user name or domain\user name format.
        permission_type (EAccountPermissionType | Unset): Permission set.
        permission_scope (list[str] | Unset): Array of users.
    """

    owner: str
    permission_type: EAccountPermissionType | Unset = UNSET
    permission_scope: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        owner = self.owner

        permission_type: str | Unset = UNSET
        if not isinstance(self.permission_type, Unset):
            permission_type = self.permission_type.value

        permission_scope: list[str] | Unset = UNSET
        if not isinstance(self.permission_scope, Unset):
            permission_scope = self.permission_scope

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "owner": owner,
            }
        )
        if permission_type is not UNSET:
            field_dict["permissionType"] = permission_type
        if permission_scope is not UNSET:
            field_dict["permissionScope"] = permission_scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        owner = d.pop("owner")

        _permission_type = d.pop("permissionType", UNSET)
        permission_type: EAccountPermissionType | Unset
        if isinstance(_permission_type, Unset):
            permission_type = UNSET
        else:
            permission_type = EAccountPermissionType(_permission_type)

        permission_scope = cast(list[str], d.pop("permissionScope", UNSET))

        unstructured_data_restore_permissions_model = cls(
            owner=owner,
            permission_type=permission_type,
            permission_scope=permission_scope,
        )

        unstructured_data_restore_permissions_model.additional_properties = d
        return unstructured_data_restore_permissions_model

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
