from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel


T = TypeVar("T", bound="LinuxAgentGuestOsCredentialsPerMachineModel")


@_attrs_define
class LinuxAgentGuestOsCredentialsPerMachineModel:
    """Settings for per-machine guest OS credentials.

    Attributes:
        credentials_id (UUID | Unset): Credentials ID.
        machine_object (AgentObjectModel | Unset): Agent-managed object.
        default (bool | Unset): If `true`, Veeam Backup & Replication will use job-level credentials.
    """

    credentials_id: UUID | Unset = UNSET
    machine_object: AgentObjectModel | Unset = UNSET
    default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        machine_object: dict[str, Any] | Unset = UNSET
        if not isinstance(self.machine_object, Unset):
            machine_object = self.machine_object.to_dict()

        default = self.default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if machine_object is not UNSET:
            field_dict["machineObject"] = machine_object
        if default is not UNSET:
            field_dict["default"] = default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel

        d = dict(src_dict)
        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _machine_object = d.pop("machineObject", UNSET)
        machine_object: AgentObjectModel | Unset
        if isinstance(_machine_object, Unset):
            machine_object = UNSET
        else:
            machine_object = AgentObjectModel.from_dict(_machine_object)

        default = d.pop("default", UNSET)

        linux_agent_guest_os_credentials_per_machine_model = cls(
            credentials_id=credentials_id,
            machine_object=machine_object,
            default=default,
        )

        linux_agent_guest_os_credentials_per_machine_model.additional_properties = d
        return linux_agent_guest_os_credentials_per_machine_model

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
