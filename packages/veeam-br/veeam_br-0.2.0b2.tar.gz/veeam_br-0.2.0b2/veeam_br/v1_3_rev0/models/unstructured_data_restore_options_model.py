from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_restore_permissions_model import UnstructuredDataRestorePermissionsModel


T = TypeVar("T", bound="UnstructuredDataRestoreOptionsModel")


@_attrs_define
class UnstructuredDataRestoreOptionsModel:
    """Options for unstructured data restore.

    Attributes:
        restore_point_id (UUID): Restore point ID.
        mount_server_id (UUID | Unset): Mount server ID.
        permissions (UnstructuredDataRestorePermissionsModel | Unset): Permissions for restoring unstructured data.
    """

    restore_point_id: UUID
    mount_server_id: UUID | Unset = UNSET
    permissions: UnstructuredDataRestorePermissionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        mount_server_id: str | Unset = UNSET
        if not isinstance(self.mount_server_id, Unset):
            mount_server_id = str(self.mount_server_id)

        permissions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = self.permissions.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
            }
        )
        if mount_server_id is not UNSET:
            field_dict["mountServerId"] = mount_server_id
        if permissions is not UNSET:
            field_dict["permissions"] = permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_restore_permissions_model import UnstructuredDataRestorePermissionsModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        _mount_server_id = d.pop("mountServerId", UNSET)
        mount_server_id: UUID | Unset
        if isinstance(_mount_server_id, Unset):
            mount_server_id = UNSET
        else:
            mount_server_id = UUID(_mount_server_id)

        _permissions = d.pop("permissions", UNSET)
        permissions: UnstructuredDataRestorePermissionsModel | Unset
        if isinstance(_permissions, Unset):
            permissions = UNSET
        else:
            permissions = UnstructuredDataRestorePermissionsModel.from_dict(_permissions)

        unstructured_data_restore_options_model = cls(
            restore_point_id=restore_point_id,
            mount_server_id=mount_server_id,
            permissions=permissions,
        )

        unstructured_data_restore_options_model.additional_properties = d
        return unstructured_data_restore_options_model

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
