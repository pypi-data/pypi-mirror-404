from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ADDomainModel")


@_attrs_define
class ADDomainModel:
    """Settings of Active Directory domain.

    Attributes:
        id (UUID): ID of Active Directory domain.
        name (str): Name of Active Directory domain.
        server_name (str): DNS name or IP address of Active Directory server.
        credentials_id (UUID): Credentials ID.
        port (int | Unset): Port used to connect to the domain.
    """

    id: UUID
    name: str
    server_name: str
    credentials_id: UUID
    port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        server_name = self.server_name

        credentials_id = str(self.credentials_id)

        port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "serverName": server_name,
                "credentialsId": credentials_id,
            }
        )
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        server_name = d.pop("serverName")

        credentials_id = UUID(d.pop("credentialsId"))

        port = d.pop("port", UNSET)

        ad_domain_model = cls(
            id=id,
            name=name,
            server_name=server_name,
            credentials_id=credentials_id,
            port=port,
        )

        ad_domain_model.additional_properties = d
        return ad_domain_model

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
