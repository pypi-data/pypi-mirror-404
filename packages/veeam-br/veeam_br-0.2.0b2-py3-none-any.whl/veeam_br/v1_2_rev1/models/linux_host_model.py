from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_storage_type import ECredentialsStorageType
from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_credentials_spec import LinuxCredentialsSpec
    from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel


T = TypeVar("T", bound="LinuxHostModel")


@_attrs_define
class LinuxHostModel:
    """
    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_storage_type (ECredentialsStorageType): Credentials type used to connect to the Linux server.
        credentials_id (UUID | Unset): Permanent credentials ID.
        single_use_credentials (LinuxCredentialsSpec | Unset): Single-use credentials.
        ssh_settings (LinuxHostSSHSettingsModel | Unset): SSH settings.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_storage_type: ECredentialsStorageType
    credentials_id: UUID | Unset = UNSET
    single_use_credentials: LinuxCredentialsSpec | Unset = UNSET
    ssh_settings: LinuxHostSSHSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_storage_type = self.credentials_storage_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        single_use_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.single_use_credentials, Unset):
            single_use_credentials = self.single_use_credentials.to_dict()

        ssh_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ssh_settings, Unset):
            ssh_settings = self.ssh_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
                "credentialsStorageType": credentials_storage_type,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if single_use_credentials is not UNSET:
            field_dict["singleUseCredentials"] = single_use_credentials
        if ssh_settings is not UNSET:
            field_dict["sshSettings"] = ssh_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_credentials_spec import LinuxCredentialsSpec
        from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_storage_type = ECredentialsStorageType(d.pop("credentialsStorageType"))

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

        _ssh_settings = d.pop("sshSettings", UNSET)
        ssh_settings: LinuxHostSSHSettingsModel | Unset
        if isinstance(_ssh_settings, Unset):
            ssh_settings = UNSET
        else:
            ssh_settings = LinuxHostSSHSettingsModel.from_dict(_ssh_settings)

        linux_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_storage_type=credentials_storage_type,
            credentials_id=credentials_id,
            single_use_credentials=single_use_credentials,
            ssh_settings=ssh_settings,
        )

        linux_host_model.additional_properties = d
        return linux_host_model

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
