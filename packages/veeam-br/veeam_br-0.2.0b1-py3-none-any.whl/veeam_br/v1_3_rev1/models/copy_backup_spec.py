from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CopyBackupSpec")


@_attrs_define
class CopyBackupSpec:
    """Backup copy settings.

    Attributes:
        backup_ids (list[UUID]): Array of backup IDs whose data you want to copy. To get the IDs, run the [Get All
            Backups](Backups#operation/GetAllBackups) request.
        backup_repository (UUID): Backup repository name.
        archive_repository (UUID | Unset): Archive repository name.
    """

    backup_ids: list[UUID]
    backup_repository: UUID
    archive_repository: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_ids = []
        for backup_ids_item_data in self.backup_ids:
            backup_ids_item = str(backup_ids_item_data)
            backup_ids.append(backup_ids_item)

        backup_repository = str(self.backup_repository)

        archive_repository: str | Unset = UNSET
        if not isinstance(self.archive_repository, Unset):
            archive_repository = str(self.archive_repository)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupIds": backup_ids,
                "backupRepository": backup_repository,
            }
        )
        if archive_repository is not UNSET:
            field_dict["archiveRepository"] = archive_repository

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        backup_ids = []
        _backup_ids = d.pop("backupIds")
        for backup_ids_item_data in _backup_ids:
            backup_ids_item = UUID(backup_ids_item_data)

            backup_ids.append(backup_ids_item)

        backup_repository = UUID(d.pop("backupRepository"))

        _archive_repository = d.pop("archiveRepository", UNSET)
        archive_repository: UUID | Unset
        if isinstance(_archive_repository, Unset):
            archive_repository = UNSET
        else:
            archive_repository = UUID(_archive_repository)

        copy_backup_spec = cls(
            backup_ids=backup_ids,
            backup_repository=backup_repository,
            archive_repository=archive_repository,
        )

        copy_backup_spec.additional_properties = d
        return copy_backup_spec

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
