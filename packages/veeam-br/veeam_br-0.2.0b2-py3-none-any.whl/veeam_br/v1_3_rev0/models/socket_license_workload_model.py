from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_socket_license_object_type import ESocketLicenseObjectType

T = TypeVar("T", bound="SocketLicenseWorkloadModel")


@_attrs_define
class SocketLicenseWorkloadModel:
    """Details on host covered by socket licenses.

    Attributes:
        name (str): Name of the protected workload.
        host_name (str): Name of the host.
        host_id (UUID): ID of the host.
        sockets_number (int): Number of CPU sockets on the host.
        cores_number (int): Number of CPU cores on the host.
        type_ (ESocketLicenseObjectType): Type of host covered by socket license.
    """

    name: str
    host_name: str
    host_id: UUID
    sockets_number: int
    cores_number: int
    type_: ESocketLicenseObjectType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        host_name = self.host_name

        host_id = str(self.host_id)

        sockets_number = self.sockets_number

        cores_number = self.cores_number

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "hostName": host_name,
                "hostId": host_id,
                "socketsNumber": sockets_number,
                "coresNumber": cores_number,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        host_name = d.pop("hostName")

        host_id = UUID(d.pop("hostId"))

        sockets_number = d.pop("socketsNumber")

        cores_number = d.pop("coresNumber")

        type_ = ESocketLicenseObjectType(d.pop("type"))

        socket_license_workload_model = cls(
            name=name,
            host_name=host_name,
            host_id=host_id,
            sockets_number=sockets_number,
            cores_number=cores_number,
            type_=type_,
        )

        socket_license_workload_model.additional_properties = d
        return socket_license_workload_model

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
