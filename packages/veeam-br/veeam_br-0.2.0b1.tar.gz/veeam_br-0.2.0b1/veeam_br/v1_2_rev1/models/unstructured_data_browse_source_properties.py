from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataBrowseSourceProperties")


@_attrs_define
class UnstructuredDataBrowseSourceProperties:
    """Properties of unstructured data backup.

    Attributes:
        backup_id (UUID | Unset): Backup ID.
    """

    backup_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_id: str | Unset = UNSET
        if not isinstance(self.backup_id, Unset):
            backup_id = str(self.backup_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_id is not UNSET:
            field_dict["backupId"] = backup_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _backup_id = d.pop("backupId", UNSET)
        backup_id: UUID | Unset
        if isinstance(_backup_id, Unset):
            backup_id = UNSET
        else:
            backup_id = UUID(_backup_id)

        unstructured_data_browse_source_properties = cls(
            backup_id=backup_id,
        )

        unstructured_data_browse_source_properties.additional_properties = d
        return unstructured_data_browse_source_properties

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
