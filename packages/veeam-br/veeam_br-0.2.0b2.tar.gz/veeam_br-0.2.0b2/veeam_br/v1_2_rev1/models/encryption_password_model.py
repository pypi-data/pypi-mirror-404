from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="EncryptionPasswordModel")


@_attrs_define
class EncryptionPasswordModel:
    """
    Attributes:
        id (UUID): ID of the encryption password.
        hint (str): Hint for the encryption password.
        modification_time (datetime.datetime | Unset): Date and time when the password was last modified.
        unique_id (str | Unset): Unique ID for the encryption password.
    """

    id: UUID
    hint: str
    modification_time: datetime.datetime | Unset = UNSET
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        hint = self.hint

        modification_time: str | Unset = UNSET
        if not isinstance(self.modification_time, Unset):
            modification_time = self.modification_time.isoformat()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "hint": hint,
            }
        )
        if modification_time is not UNSET:
            field_dict["modificationTime"] = modification_time
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        hint = d.pop("hint")

        _modification_time = d.pop("modificationTime", UNSET)
        modification_time: datetime.datetime | Unset
        if isinstance(_modification_time, Unset):
            modification_time = UNSET
        else:
            modification_time = isoparse(_modification_time)

        unique_id = d.pop("uniqueId", UNSET)

        encryption_password_model = cls(
            id=id,
            hint=hint,
            modification_time=modification_time,
            unique_id=unique_id,
        )

        encryption_password_model.additional_properties = d
        return encryption_password_model

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
