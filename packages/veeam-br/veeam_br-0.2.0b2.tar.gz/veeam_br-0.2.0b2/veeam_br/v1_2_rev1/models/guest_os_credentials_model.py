from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guest_os_credentials_per_machine_model import GuestOsCredentialsPerMachineModel


T = TypeVar("T", bound="GuestOsCredentialsModel")


@_attrs_define
class GuestOsCredentialsModel:
    """VM custom credentials.

    Attributes:
        credentials_id (UUID): Credentials ID for Microsoft Windows VMs.
        credentials_type (ECredentialsType): Credentials type.
        credentials_per_machine (list[GuestOsCredentialsPerMachineModel] | Unset): Individual credentials for VMs.
    """

    credentials_id: UUID
    credentials_type: ECredentialsType
    credentials_per_machine: list[GuestOsCredentialsPerMachineModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        credentials_type = self.credentials_type.value

        credentials_per_machine: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.credentials_per_machine, Unset):
            credentials_per_machine = []
            for credentials_per_machine_item_data in self.credentials_per_machine:
                credentials_per_machine_item = credentials_per_machine_item_data.to_dict()
                credentials_per_machine.append(credentials_per_machine_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "credentialsType": credentials_type,
            }
        )
        if credentials_per_machine is not UNSET:
            field_dict["credentialsPerMachine"] = credentials_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.guest_os_credentials_per_machine_model import GuestOsCredentialsPerMachineModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        credentials_type = ECredentialsType(d.pop("credentialsType"))

        _credentials_per_machine = d.pop("credentialsPerMachine", UNSET)
        credentials_per_machine: list[GuestOsCredentialsPerMachineModel] | Unset = UNSET
        if _credentials_per_machine is not UNSET:
            credentials_per_machine = []
            for credentials_per_machine_item_data in _credentials_per_machine:
                credentials_per_machine_item = GuestOsCredentialsPerMachineModel.from_dict(
                    credentials_per_machine_item_data
                )

                credentials_per_machine.append(credentials_per_machine_item)

        guest_os_credentials_model = cls(
            credentials_id=credentials_id,
            credentials_type=credentials_type,
            credentials_per_machine=credentials_per_machine,
        )

        guest_os_credentials_model.additional_properties = d
        return guest_os_credentials_model

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
