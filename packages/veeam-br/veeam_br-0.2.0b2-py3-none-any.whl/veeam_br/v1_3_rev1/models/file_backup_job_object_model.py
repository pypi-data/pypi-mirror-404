from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FileBackupJobObjectModel")


@_attrs_define
class FileBackupJobObjectModel:
    """File share processed by the job.

    Attributes:
        file_server_id (UUID): File share ID. To get the ID, run the [Get All Unstructured Data Servers](Inventory-
            Browser#operation/GetAllUnstructuredDataServers) request.
        path (str | Unset): Path to folders and files.
        inclusion_mask (list[str] | Unset): Array of folders and files added to the file share backup job. Full paths to
            files and folders, environmental variables and file masks with the asterisk (*) and question mark (?) characters
            can be used.
        exclusion_mask (list[str] | Unset): Array of folders and files not added to the file share backup job. Full
            paths to files and folders, environmental variables and file masks with the asterisk (*) and question mark (?)
            characters can be used.
    """

    file_server_id: UUID
    path: str | Unset = UNSET
    inclusion_mask: list[str] | Unset = UNSET
    exclusion_mask: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_server_id = str(self.file_server_id)

        path = self.path

        inclusion_mask: list[str] | Unset = UNSET
        if not isinstance(self.inclusion_mask, Unset):
            inclusion_mask = self.inclusion_mask

        exclusion_mask: list[str] | Unset = UNSET
        if not isinstance(self.exclusion_mask, Unset):
            exclusion_mask = self.exclusion_mask

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fileServerId": file_server_id,
            }
        )
        if path is not UNSET:
            field_dict["path"] = path
        if inclusion_mask is not UNSET:
            field_dict["inclusionMask"] = inclusion_mask
        if exclusion_mask is not UNSET:
            field_dict["exclusionMask"] = exclusion_mask

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_server_id = UUID(d.pop("fileServerId"))

        path = d.pop("path", UNSET)

        inclusion_mask = cast(list[str], d.pop("inclusionMask", UNSET))

        exclusion_mask = cast(list[str], d.pop("exclusionMask", UNSET))

        file_backup_job_object_model = cls(
            file_server_id=file_server_id,
            path=path,
            inclusion_mask=inclusion_mask,
            exclusion_mask=exclusion_mask,
        )

        file_backup_job_object_model.additional_properties = d
        return file_backup_job_object_model

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
