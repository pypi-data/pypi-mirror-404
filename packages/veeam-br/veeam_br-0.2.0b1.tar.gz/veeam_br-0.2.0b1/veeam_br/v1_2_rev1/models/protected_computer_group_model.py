from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ProtectedComputerGroupModel")


@_attrs_define
class ProtectedComputerGroupModel:
    """
    Attributes:
        id (UUID): ID of the protection group.
        name (str): Type of the protection group.
        credentials_id (UUID): Default credentials that are used to connect to computers included in the protection
            group.
    """

    id: UUID
    name: str
    credentials_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        credentials_id = str(self.credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "credentialsId": credentials_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        credentials_id = UUID(d.pop("credentialsId"))

        protected_computer_group_model = cls(
            id=id,
            name=name,
            credentials_id=credentials_id,
        )

        protected_computer_group_model.additional_properties = d
        return protected_computer_group_model

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
