from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BackupObjectPair")


@_attrs_define
class BackupObjectPair:
    """Contains backup ID and backup object ID.

    Attributes:
        backup_id (UUID): ID of the backup.
        backup_object_id (UUID): ID of the backup object.
    """

    backup_id: UUID
    backup_object_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_id = str(self.backup_id)

        backup_object_id = str(self.backup_object_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupId": backup_id,
                "backupObjectId": backup_object_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        backup_id = UUID(d.pop("backupId"))

        backup_object_id = UUID(d.pop("backupObjectId"))

        backup_object_pair = cls(
            backup_id=backup_id,
            backup_object_id=backup_object_id,
        )

        backup_object_pair.additional_properties = d
        return backup_object_pair

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
