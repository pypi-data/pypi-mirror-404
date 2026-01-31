from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_authentication_type import EAuthenticationType
from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="LinuxCredentialsSpec")


@_attrs_define
class LinuxCredentialsSpec:
    """Settings for single-use credentials.

    Attributes:
        username (str): User name.
        type_ (ECredentialsType): Credentials type.
        authentication_type (EAuthenticationType): Type of the authentication used for Linux credentials.
        description (str | Unset): Description of the credentials record.
        unique_id (str | Unset): Unique ID that identifies the credentials record.
        ssh_port (int | Unset): SSH port used to connect to a Linux server.
        elevate_to_root (bool | Unset): If `true`, the permissions of the account are automatically elevated to the root
            user.
        add_to_sudoers (bool | Unset): If `true`, the account is automatically added to the sudoers file.
        use_su (bool | Unset): If `true`, the `su` command is used for Linux distributions where the `sudo` command is
            not available.
        private_key (str | Unset): Private key.
        passphrase (str | Unset): Passphrase that protects the private key.
        password (str | Unset): Password.
        root_password (str | Unset): Password for the root account.
    """

    username: str
    type_: ECredentialsType
    authentication_type: EAuthenticationType
    description: str | Unset = UNSET
    unique_id: str | Unset = UNSET
    ssh_port: int | Unset = UNSET
    elevate_to_root: bool | Unset = UNSET
    add_to_sudoers: bool | Unset = UNSET
    use_su: bool | Unset = UNSET
    private_key: str | Unset = UNSET
    passphrase: str | Unset = UNSET
    password: str | Unset = UNSET
    root_password: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        type_ = self.type_.value

        authentication_type = self.authentication_type.value

        description = self.description

        unique_id = self.unique_id

        ssh_port = self.ssh_port

        elevate_to_root = self.elevate_to_root

        add_to_sudoers = self.add_to_sudoers

        use_su = self.use_su

        private_key = self.private_key

        passphrase = self.passphrase

        password = self.password

        root_password = self.root_password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "type": type_,
                "authenticationType": authentication_type,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id
        if ssh_port is not UNSET:
            field_dict["SSHPort"] = ssh_port
        if elevate_to_root is not UNSET:
            field_dict["elevateToRoot"] = elevate_to_root
        if add_to_sudoers is not UNSET:
            field_dict["addToSudoers"] = add_to_sudoers
        if use_su is not UNSET:
            field_dict["useSu"] = use_su
        if private_key is not UNSET:
            field_dict["privateKey"] = private_key
        if passphrase is not UNSET:
            field_dict["passphrase"] = passphrase
        if password is not UNSET:
            field_dict["password"] = password
        if root_password is not UNSET:
            field_dict["rootPassword"] = root_password

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        username = d.pop("username")

        type_ = ECredentialsType(d.pop("type"))

        authentication_type = EAuthenticationType(d.pop("authenticationType"))

        description = d.pop("description", UNSET)

        unique_id = d.pop("uniqueId", UNSET)

        ssh_port = d.pop("SSHPort", UNSET)

        elevate_to_root = d.pop("elevateToRoot", UNSET)

        add_to_sudoers = d.pop("addToSudoers", UNSET)

        use_su = d.pop("useSu", UNSET)

        private_key = d.pop("privateKey", UNSET)

        passphrase = d.pop("passphrase", UNSET)

        password = d.pop("password", UNSET)

        root_password = d.pop("rootPassword", UNSET)

        linux_credentials_spec = cls(
            username=username,
            type_=type_,
            authentication_type=authentication_type,
            description=description,
            unique_id=unique_id,
            ssh_port=ssh_port,
            elevate_to_root=elevate_to_root,
            add_to_sudoers=add_to_sudoers,
            use_su=use_su,
            private_key=private_key,
            passphrase=passphrase,
            password=password,
            root_password=root_password,
        )

        linux_credentials_spec.additional_properties = d
        return linux_credentials_spec

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
