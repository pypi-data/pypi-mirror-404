from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataShareRestoreDestinationModel")


@_attrs_define
class UnstructuredDataShareRestoreDestinationModel:
    """Target for restoring entire file share.

    Attributes:
        unstructured_data_server_id (UUID | Unset): ID of the target file share. To get the ID, run the [Get All
            Unstructured Data Servers](Inventory-Browser#operation/GetAllUnstructuredDataServers) request.
        restore_to_backup_server (bool | Unset): If `true`, the contents of the file share will be restored to the
            backup server.
        path (str | Unset): Path to the folder on the selected file share to which files will be restored.
        preserve_hierarchy (bool | Unset): If `true`, the folder hierarchy of the original file share will be kept in
            the new location.
    """

    unstructured_data_server_id: UUID | Unset = UNSET
    restore_to_backup_server: bool | Unset = UNSET
    path: str | Unset = UNSET
    preserve_hierarchy: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        unstructured_data_server_id: str | Unset = UNSET
        if not isinstance(self.unstructured_data_server_id, Unset):
            unstructured_data_server_id = str(self.unstructured_data_server_id)

        restore_to_backup_server = self.restore_to_backup_server

        path = self.path

        preserve_hierarchy = self.preserve_hierarchy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if unstructured_data_server_id is not UNSET:
            field_dict["unstructuredDataServerId"] = unstructured_data_server_id
        if restore_to_backup_server is not UNSET:
            field_dict["restoreToBackupServer"] = restore_to_backup_server
        if path is not UNSET:
            field_dict["path"] = path
        if preserve_hierarchy is not UNSET:
            field_dict["preserveHierarchy"] = preserve_hierarchy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _unstructured_data_server_id = d.pop("unstructuredDataServerId", UNSET)
        unstructured_data_server_id: UUID | Unset
        if isinstance(_unstructured_data_server_id, Unset):
            unstructured_data_server_id = UNSET
        else:
            unstructured_data_server_id = UUID(_unstructured_data_server_id)

        restore_to_backup_server = d.pop("restoreToBackupServer", UNSET)

        path = d.pop("path", UNSET)

        preserve_hierarchy = d.pop("preserveHierarchy", UNSET)

        unstructured_data_share_restore_destination_model = cls(
            unstructured_data_server_id=unstructured_data_server_id,
            restore_to_backup_server=restore_to_backup_server,
            path=path,
            preserve_hierarchy=preserve_hierarchy,
        )

        unstructured_data_share_restore_destination_model.additional_properties = d
        return unstructured_data_share_restore_destination_model

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
