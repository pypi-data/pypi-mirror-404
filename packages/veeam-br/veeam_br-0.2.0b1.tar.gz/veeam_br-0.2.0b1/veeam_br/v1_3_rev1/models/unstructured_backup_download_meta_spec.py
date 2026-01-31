from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredBackupDownloadMetaSpec")


@_attrs_define
class UnstructuredBackupDownloadMetaSpec:
    """Settings for downloading backup metadata.

    Attributes:
        target_repository_id (UUID | Unset): ID of the repository where the backup metadata will be stored.
    """

    target_repository_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        target_repository_id: str | Unset = UNSET
        if not isinstance(self.target_repository_id, Unset):
            target_repository_id = str(self.target_repository_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if target_repository_id is not UNSET:
            field_dict["targetRepositoryId"] = target_repository_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _target_repository_id = d.pop("targetRepositoryId", UNSET)
        target_repository_id: UUID | Unset
        if isinstance(_target_repository_id, Unset):
            target_repository_id = UNSET
        else:
            target_repository_id = UUID(_target_repository_id)

        unstructured_backup_download_meta_spec = cls(
            target_repository_id=target_repository_id,
        )

        unstructured_backup_download_meta_spec.additional_properties = d
        return unstructured_backup_download_meta_spec

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
