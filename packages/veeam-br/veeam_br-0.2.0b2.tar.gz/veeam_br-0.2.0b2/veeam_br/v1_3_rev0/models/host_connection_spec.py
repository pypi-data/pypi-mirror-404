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
    from ..models.linux_credentials_spec import LinuxCredentialsSpec


T = TypeVar("T", bound="HostConnectionSpec")


@_attrs_define
class HostConnectionSpec:
    """Connection settings.

    Attributes:
        server_name (str): Full DNS name or IP address of the server.
        type_ (EManagedServerType): Type of the server.
        credentials_storage_type (ECredentialsStorageType | Unset): Credentials type used to connect to the Linux
            server.
        credentials_id (UUID | Unset): ID of a credentials record used to connect to the server.
        single_use_credentials (LinuxCredentialsSpec | Unset): Settings for single-use credentials.
        port (int | Unset): Port used to communicate with the server.
    """

    server_name: str
    type_: EManagedServerType
    credentials_storage_type: ECredentialsStorageType | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    single_use_credentials: LinuxCredentialsSpec | Unset = UNSET
    port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        server_name = self.server_name

        type_ = self.type_.value

        credentials_storage_type: str | Unset = UNSET
        if not isinstance(self.credentials_storage_type, Unset):
            credentials_storage_type = self.credentials_storage_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        single_use_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.single_use_credentials, Unset):
            single_use_credentials = self.single_use_credentials.to_dict()

        port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serverName": server_name,
                "type": type_,
            }
        )
        if credentials_storage_type is not UNSET:
            field_dict["credentialsStorageType"] = credentials_storage_type
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if single_use_credentials is not UNSET:
            field_dict["singleUseCredentials"] = single_use_credentials
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_credentials_spec import LinuxCredentialsSpec

        d = dict(src_dict)
        server_name = d.pop("serverName")

        type_ = EManagedServerType(d.pop("type"))

        _credentials_storage_type = d.pop("credentialsStorageType", UNSET)
        credentials_storage_type: ECredentialsStorageType | Unset
        if isinstance(_credentials_storage_type, Unset):
            credentials_storage_type = UNSET
        else:
            credentials_storage_type = ECredentialsStorageType(_credentials_storage_type)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _single_use_credentials = d.pop("singleUseCredentials", UNSET)
        single_use_credentials: LinuxCredentialsSpec | Unset
        if isinstance(_single_use_credentials, Unset):
            single_use_credentials = UNSET
        else:
            single_use_credentials = LinuxCredentialsSpec.from_dict(_single_use_credentials)

        port = d.pop("port", UNSET)

        host_connection_spec = cls(
            server_name=server_name,
            type_=type_,
            credentials_storage_type=credentials_storage_type,
            credentials_id=credentials_id,
            single_use_credentials=single_use_credentials,
            port=port,
        )

        host_connection_spec.additional_properties = d
        return host_connection_spec

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
