from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="EncryptionPasswordExportSpec")


@_attrs_define
class EncryptionPasswordExportSpec:
    """Export settings for data encryption passwords.

    Attributes:
        modification_time_from (datetime.datetime | Unset): Date and time when the password was last modified.
        ids (list[UUID] | Unset): Array of password IDs.
        hints (list[str] | Unset): Array of password hints.
        tags (list[str] | Unset): Array of password tags.
    """

    modification_time_from: datetime.datetime | Unset = UNSET
    ids: list[UUID] | Unset = UNSET
    hints: list[str] | Unset = UNSET
    tags: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        modification_time_from: str | Unset = UNSET
        if not isinstance(self.modification_time_from, Unset):
            modification_time_from = self.modification_time_from.isoformat()

        ids: list[str] | Unset = UNSET
        if not isinstance(self.ids, Unset):
            ids = []
            for ids_item_data in self.ids:
                ids_item = str(ids_item_data)
                ids.append(ids_item)

        hints: list[str] | Unset = UNSET
        if not isinstance(self.hints, Unset):
            hints = self.hints

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if modification_time_from is not UNSET:
            field_dict["modificationTimeFrom"] = modification_time_from
        if ids is not UNSET:
            field_dict["ids"] = ids
        if hints is not UNSET:
            field_dict["hints"] = hints
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _modification_time_from = d.pop("modificationTimeFrom", UNSET)
        modification_time_from: datetime.datetime | Unset
        if isinstance(_modification_time_from, Unset):
            modification_time_from = UNSET
        else:
            modification_time_from = isoparse(_modification_time_from)

        _ids = d.pop("ids", UNSET)
        ids: list[UUID] | Unset = UNSET
        if _ids is not UNSET:
            ids = []
            for ids_item_data in _ids:
                ids_item = UUID(ids_item_data)

                ids.append(ids_item)

        hints = cast(list[str], d.pop("hints", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        encryption_password_export_spec = cls(
            modification_time_from=modification_time_from,
            ids=ids,
            hints=hints,
            tags=tags,
        )

        encryption_password_export_spec.additional_properties = d
        return encryption_password_export_spec

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
