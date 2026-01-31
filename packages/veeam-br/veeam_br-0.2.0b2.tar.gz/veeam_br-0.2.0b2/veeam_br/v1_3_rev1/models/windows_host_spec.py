from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_storage_type import ECredentialsStorageType
from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.managed_host_ports_model import ManagedHostPortsModel


T = TypeVar("T", bound="WindowsHostSpec")


@_attrs_define
class WindowsHostSpec:
    """Microsoft Windows server settings.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials_storage_type (ECredentialsStorageType): Credentials type used to connect to the server.
        credentials_id (UUID | Unset): ID of the credentials used to connect to the server.
        network_settings (ManagedHostPortsModel | Unset): Veeam Backup & Replication components installed on the server
            and ports used by the components.
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials_storage_type: ECredentialsStorageType
    credentials_id: UUID | Unset = UNSET
    network_settings: ManagedHostPortsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials_storage_type = self.credentials_storage_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "credentialsStorageType": credentials_storage_type,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.managed_host_ports_model import ManagedHostPortsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        credentials_storage_type = ECredentialsStorageType(d.pop("credentialsStorageType"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: ManagedHostPortsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = ManagedHostPortsModel.from_dict(_network_settings)

        windows_host_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials_storage_type=credentials_storage_type,
            credentials_id=credentials_id,
            network_settings=network_settings,
        )

        windows_host_spec.additional_properties = d
        return windows_host_spec

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
