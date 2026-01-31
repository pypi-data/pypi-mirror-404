from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel


T = TypeVar("T", bound="LinuxHostImportSpec")


@_attrs_define
class LinuxHostImportSpec:
    """Settings for importing Linux-based managed server.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials (CredentialsImportModel): Credentials used for connection.
        ssh_fingerprint (str): SSH key fingerprint used to verify the server identity.
        ssh_settings (LinuxHostSSHSettingsModel | Unset): SSH settings of the Linux host.
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials: CredentialsImportModel
    ssh_fingerprint: str
    ssh_settings: LinuxHostSSHSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials = self.credentials.to_dict()

        ssh_fingerprint = self.ssh_fingerprint

        ssh_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ssh_settings, Unset):
            ssh_settings = self.ssh_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "credentials": credentials,
                "sshFingerprint": ssh_fingerprint,
            }
        )
        if ssh_settings is not UNSET:
            field_dict["sshSettings"] = ssh_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        credentials = CredentialsImportModel.from_dict(d.pop("credentials"))

        ssh_fingerprint = d.pop("sshFingerprint")

        _ssh_settings = d.pop("sshSettings", UNSET)
        ssh_settings: LinuxHostSSHSettingsModel | Unset
        if isinstance(_ssh_settings, Unset):
            ssh_settings = UNSET
        else:
            ssh_settings = LinuxHostSSHSettingsModel.from_dict(_ssh_settings)

        linux_host_import_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials=credentials,
            ssh_fingerprint=ssh_fingerprint,
            ssh_settings=ssh_settings,
        )

        linux_host_import_spec.additional_properties = d
        return linux_host_import_spec

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
