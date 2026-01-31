from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="StandardCredentialsModel")


@_attrs_define
class StandardCredentialsModel:
    """
    Attributes:
        id (UUID): ID of the credentials record.
        username (str): User name.
        description (str): Description of the credentials record.
        type_ (ECredentialsType): Credentials type.
        creation_time (datetime.datetime): Date and time when the credentials were created.
        unique_id (str | Unset): Unique ID that identifies the credentials record.
    """

    id: UUID
    username: str
    description: str
    type_: ECredentialsType
    creation_time: datetime.datetime
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        username = self.username

        description = self.description

        type_ = self.type_.value

        creation_time = self.creation_time.isoformat()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "username": username,
                "description": description,
                "type": type_,
                "creationTime": creation_time,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        username = d.pop("username")

        description = d.pop("description")

        type_ = ECredentialsType(d.pop("type"))

        creation_time = isoparse(d.pop("creationTime"))

        unique_id = d.pop("uniqueId", UNSET)

        standard_credentials_model = cls(
            id=id,
            username=username,
            description=description,
            type_=type_,
            creation_time=creation_time,
            unique_id=unique_id,
        )

        standard_credentials_model.additional_properties = d
        return standard_credentials_model

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
