from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_agent_guest_os_credentials_per_machine_model import LinuxAgentGuestOsCredentialsPerMachineModel


T = TypeVar("T", bound="LinuxAgentGuestOsCredentialsModel")


@_attrs_define
class LinuxAgentGuestOsCredentialsModel:
    """Guest OS credentials for protected Linux computer.

    Attributes:
        use_protection_group_credentials (bool | Unset): If `true`, the backup job will use the credentials specified
            when setting up the protection group.
        credentials_id (UUID | Unset): Credential record ID.
        credentials_per_machine (list[LinuxAgentGuestOsCredentialsPerMachineModel] | Unset): Array of per-machine
            credentials.
    """

    use_protection_group_credentials: bool | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    credentials_per_machine: list[LinuxAgentGuestOsCredentialsPerMachineModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_protection_group_credentials = self.use_protection_group_credentials

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        credentials_per_machine: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.credentials_per_machine, Unset):
            credentials_per_machine = []
            for credentials_per_machine_item_data in self.credentials_per_machine:
                credentials_per_machine_item = credentials_per_machine_item_data.to_dict()
                credentials_per_machine.append(credentials_per_machine_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if use_protection_group_credentials is not UNSET:
            field_dict["useProtectionGroupCredentials"] = use_protection_group_credentials
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if credentials_per_machine is not UNSET:
            field_dict["credentialsPerMachine"] = credentials_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_agent_guest_os_credentials_per_machine_model import (
            LinuxAgentGuestOsCredentialsPerMachineModel,
        )

        d = dict(src_dict)
        use_protection_group_credentials = d.pop("useProtectionGroupCredentials", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _credentials_per_machine = d.pop("credentialsPerMachine", UNSET)
        credentials_per_machine: list[LinuxAgentGuestOsCredentialsPerMachineModel] | Unset = UNSET
        if _credentials_per_machine is not UNSET:
            credentials_per_machine = []
            for credentials_per_machine_item_data in _credentials_per_machine:
                credentials_per_machine_item = LinuxAgentGuestOsCredentialsPerMachineModel.from_dict(
                    credentials_per_machine_item_data
                )

                credentials_per_machine.append(credentials_per_machine_item)

        linux_agent_guest_os_credentials_model = cls(
            use_protection_group_credentials=use_protection_group_credentials,
            credentials_id=credentials_id,
            credentials_per_machine=credentials_per_machine,
        )

        linux_agent_guest_os_credentials_model.additional_properties = d
        return linux_agent_guest_os_credentials_model

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
