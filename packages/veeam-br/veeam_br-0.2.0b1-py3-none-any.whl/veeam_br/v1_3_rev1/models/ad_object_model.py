from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ead_object_type import EADObjectType

T = TypeVar("T", bound="ADObjectModel")


@_attrs_define
class ADObjectModel:
    """Active Directory object.

    Attributes:
        id (UUID): ID of Active Directory object.
        full_name (str): Name of Active Directory object.
        domain_id (UUID): ID of Active Directory domain.
        distinguished_name (str): Distinguished name (DN) of the object.
        type_ (EADObjectType): Type of Active Directory object.
    """

    id: UUID
    full_name: str
    domain_id: UUID
    distinguished_name: str
    type_: EADObjectType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        full_name = self.full_name

        domain_id = str(self.domain_id)

        distinguished_name = self.distinguished_name

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "fullName": full_name,
                "domainId": domain_id,
                "distinguishedName": distinguished_name,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        full_name = d.pop("fullName")

        domain_id = UUID(d.pop("domainId"))

        distinguished_name = d.pop("distinguishedName")

        type_ = EADObjectType(d.pop("type"))

        ad_object_model = cls(
            id=id,
            full_name=full_name,
            domain_id=domain_id,
            distinguished_name=distinguished_name,
            type_=type_,
        )

        ad_object_model.additional_properties = d
        return ad_object_model

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
