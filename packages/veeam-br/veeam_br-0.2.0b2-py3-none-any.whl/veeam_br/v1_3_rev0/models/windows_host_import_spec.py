from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.managed_host_ports_model import ManagedHostPortsModel


T = TypeVar("T", bound="WindowsHostImportSpec")


@_attrs_define
class WindowsHostImportSpec:
    """Settings for importing Microsoft Windows-based managed server.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials (CredentialsImportModel | Unset): Credentials used for connection.
        network_settings (ManagedHostPortsModel | Unset): Veeam Backup & Replication components installed on the server
            and ports used by the components.
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials: CredentialsImportModel | Unset = UNSET
    network_settings: ManagedHostPortsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.credentials, Unset):
            credentials = self.credentials.to_dict()

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
            }
        )
        if credentials is not UNSET:
            field_dict["credentials"] = credentials
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.managed_host_ports_model import ManagedHostPortsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        _credentials = d.pop("credentials", UNSET)
        credentials: CredentialsImportModel | Unset
        if isinstance(_credentials, Unset):
            credentials = UNSET
        else:
            credentials = CredentialsImportModel.from_dict(_credentials)

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: ManagedHostPortsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = ManagedHostPortsModel.from_dict(_network_settings)

        windows_host_import_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials=credentials,
            network_settings=network_settings,
        )

        windows_host_import_spec.additional_properties = d
        return windows_host_import_spec

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
