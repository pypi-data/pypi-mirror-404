from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus

T = TypeVar("T", bound="ManagedServerModel")


@_attrs_define
class ManagedServerModel:
    """Managed server.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        managed_server_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
        )

        managed_server_model.additional_properties = d
        return managed_server_model

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
