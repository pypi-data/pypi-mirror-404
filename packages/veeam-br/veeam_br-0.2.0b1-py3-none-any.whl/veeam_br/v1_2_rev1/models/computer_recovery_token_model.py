from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComputerRecoveryTokenModel")


@_attrs_define
class ComputerRecoveryTokenModel:
    """
    Attributes:
        id (UUID): ID of the recovery token.
        name (str): Friendly name of the recovery token.
        expiration_date (datetime.datetime): Date and time when the recovery token expires.
        recovery_token (str | Unset): Recovery token.
    """

    id: UUID
    name: str
    expiration_date: datetime.datetime
    recovery_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        expiration_date = self.expiration_date.isoformat()

        recovery_token = self.recovery_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "expirationDate": expiration_date,
            }
        )
        if recovery_token is not UNSET:
            field_dict["recoveryToken"] = recovery_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        expiration_date = isoparse(d.pop("expirationDate"))

        recovery_token = d.pop("recoveryToken", UNSET)

        computer_recovery_token_model = cls(
            id=id,
            name=name,
            expiration_date=expiration_date,
            recovery_token=recovery_token,
        )

        computer_recovery_token_model.additional_properties = d
        return computer_recovery_token_model

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
