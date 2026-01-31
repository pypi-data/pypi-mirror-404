from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="LinuxCredentialsModel")


@_attrs_define
class LinuxCredentialsModel:
    """
    Attributes:
        id (UUID): ID of the credentials record.
        username (str): User name.
        description (str): Description of the credentials record.
        type_ (ECredentialsType): Credentials type.
        creation_time (datetime.datetime): Date and time when the credentials were created.
        unique_id (str | Unset): Unique ID that identifies the credentials record.
        ssh_port (int | Unset): SSH port used to connect to a Linux server.
        elevate_to_root (bool | Unset): If `true`, the permissions of the account are automatically elevated to the root
            user.
        add_to_sudoers (bool | Unset): If `true`, the account is automatically added to the sudoers file.
        use_su (bool | Unset): If `true`, the `su` command is used for Linux distributions where the `sudo` command is
            not available.
        private_key (str | Unset): Private key.
        passphrase (str | Unset): Passphrase that protects the private key.
    """

    id: UUID
    username: str
    description: str
    type_: ECredentialsType
    creation_time: datetime.datetime
    unique_id: str | Unset = UNSET
    ssh_port: int | Unset = UNSET
    elevate_to_root: bool | Unset = UNSET
    add_to_sudoers: bool | Unset = UNSET
    use_su: bool | Unset = UNSET
    private_key: str | Unset = UNSET
    passphrase: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        username = self.username

        description = self.description

        type_ = self.type_.value

        creation_time = self.creation_time.isoformat()

        unique_id = self.unique_id

        ssh_port = self.ssh_port

        elevate_to_root = self.elevate_to_root

        add_to_sudoers = self.add_to_sudoers

        use_su = self.use_su

        private_key = self.private_key

        passphrase = self.passphrase

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "username": username,
                "description": description,
                "type": type_,
                "creationTime": creation_time,
            }
        )
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        username = d.pop("username")

        description = d.pop("description")

        type_ = ECredentialsType(d.pop("type"))

        creation_time = isoparse(d.pop("creationTime"))

        unique_id = d.pop("uniqueId", UNSET)

        ssh_port = d.pop("SSHPort", UNSET)

        elevate_to_root = d.pop("elevateToRoot", UNSET)

        add_to_sudoers = d.pop("addToSudoers", UNSET)

        use_su = d.pop("useSu", UNSET)

        private_key = d.pop("privateKey", UNSET)

        passphrase = d.pop("passphrase", UNSET)

        linux_credentials_model = cls(
            id=id,
            username=username,
            description=description,
            type_=type_,
            creation_time=creation_time,
            unique_id=unique_id,
            ssh_port=ssh_port,
            elevate_to_root=elevate_to_root,
            add_to_sudoers=add_to_sudoers,
            use_su=use_su,
            private_key=private_key,
            passphrase=passphrase,
        )

        linux_credentials_model.additional_properties = d
        return linux_credentials_model

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
