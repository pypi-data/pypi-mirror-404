from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..models.e_vi_host_type import EViHostType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ViHostModel")


@_attrs_define
class ViHostModel:
    """VMware vSphere server.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_id (UUID): ID of the credentials used to connect to the server.
        port (int): Port used to communicate with the server.
        vi_host_type (EViHostType | Unset): Type of the VMware vSphere server.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_id: UUID
    port: int
    vi_host_type: EViHostType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_id = str(self.credentials_id)

        port = self.port

        vi_host_type: str | Unset = UNSET
        if not isinstance(self.vi_host_type, Unset):
            vi_host_type = self.vi_host_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
                "credentialsId": credentials_id,
                "port": port,
            }
        )
        if vi_host_type is not UNSET:
            field_dict["viHostType"] = vi_host_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_id = UUID(d.pop("credentialsId"))

        port = d.pop("port")

        _vi_host_type = d.pop("viHostType", UNSET)
        vi_host_type: EViHostType | Unset
        if isinstance(_vi_host_type, Unset):
            vi_host_type = UNSET
        else:
            vi_host_type = EViHostType(_vi_host_type)

        vi_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_id=credentials_id,
            port=port,
            vi_host_type=vi_host_type,
        )

        vi_host_model.additional_properties = d
        return vi_host_model

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
