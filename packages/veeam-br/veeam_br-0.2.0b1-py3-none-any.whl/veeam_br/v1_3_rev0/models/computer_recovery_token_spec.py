from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ComputerRecoveryTokenSpec")


@_attrs_define
class ComputerRecoveryTokenSpec:
    """Recovery token settings.

    Attributes:
        backup_ids (list[UUID]): Array of backup IDs whose data you want to restore with the recovery token.
        expiration_date (datetime.datetime): Date and time when the recovery token expires.
    """

    backup_ids: list[UUID]
    expiration_date: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_ids = []
        for backup_ids_item_data in self.backup_ids:
            backup_ids_item = str(backup_ids_item_data)
            backup_ids.append(backup_ids_item)

        expiration_date = self.expiration_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupIds": backup_ids,
                "expirationDate": expiration_date,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        backup_ids = []
        _backup_ids = d.pop("backupIds")
        for backup_ids_item_data in _backup_ids:
            backup_ids_item = UUID(backup_ids_item_data)

            backup_ids.append(backup_ids_item)

        expiration_date = isoparse(d.pop("expirationDate"))

        computer_recovery_token_spec = cls(
            backup_ids=backup_ids,
            expiration_date=expiration_date,
        )

        computer_recovery_token_spec.additional_properties = d
        return computer_recovery_token_spec

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
