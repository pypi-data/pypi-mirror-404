from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.windows_host_ports_model import WindowsHostPortsModel


T = TypeVar("T", bound="WindowsHostModel")


@_attrs_define
class WindowsHostModel:
    """
    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_id (UUID): ID of the credentials used to connect to the server.
        network_settings (WindowsHostPortsModel | Unset): Veeam Backup & Replication components installed on the server
            and ports used by the components.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_id: UUID
    network_settings: WindowsHostPortsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_id = str(self.credentials_id)

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

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
            }
        )
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.windows_host_ports_model import WindowsHostPortsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_id = UUID(d.pop("credentialsId"))

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: WindowsHostPortsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = WindowsHostPortsModel.from_dict(_network_settings)

        windows_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_id=credentials_id,
            network_settings=network_settings,
        )

        windows_host_model.additional_properties = d
        return windows_host_model

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
