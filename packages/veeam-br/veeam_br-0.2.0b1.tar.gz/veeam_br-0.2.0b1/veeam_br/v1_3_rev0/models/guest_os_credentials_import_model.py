from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.guest_os_credentials_per_machine_import_model import GuestOsCredentialsPerMachineImportModel


T = TypeVar("T", bound="GuestOsCredentialsImportModel")


@_attrs_define
class GuestOsCredentialsImportModel:
    """VM custom credentials.

    Attributes:
        creds (CredentialsImportModel | Unset): Credentials used for connection.
        credentials_per_machine (list[GuestOsCredentialsPerMachineImportModel] | Unset): Array of per-machine
            credentials.
    """

    creds: CredentialsImportModel | Unset = UNSET
    credentials_per_machine: list[GuestOsCredentialsPerMachineImportModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        creds: dict[str, Any] | Unset = UNSET
        if not isinstance(self.creds, Unset):
            creds = self.creds.to_dict()

        credentials_per_machine: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.credentials_per_machine, Unset):
            credentials_per_machine = []
            for credentials_per_machine_item_data in self.credentials_per_machine:
                credentials_per_machine_item = credentials_per_machine_item_data.to_dict()
                credentials_per_machine.append(credentials_per_machine_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if creds is not UNSET:
            field_dict["creds"] = creds
        if credentials_per_machine is not UNSET:
            field_dict["credentialsPerMachine"] = credentials_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.guest_os_credentials_per_machine_import_model import GuestOsCredentialsPerMachineImportModel

        d = dict(src_dict)
        _creds = d.pop("creds", UNSET)
        creds: CredentialsImportModel | Unset
        if isinstance(_creds, Unset):
            creds = UNSET
        else:
            creds = CredentialsImportModel.from_dict(_creds)

        _credentials_per_machine = d.pop("credentialsPerMachine", UNSET)
        credentials_per_machine: list[GuestOsCredentialsPerMachineImportModel] | Unset = UNSET
        if _credentials_per_machine is not UNSET:
            credentials_per_machine = []
            for credentials_per_machine_item_data in _credentials_per_machine:
                credentials_per_machine_item = GuestOsCredentialsPerMachineImportModel.from_dict(
                    credentials_per_machine_item_data
                )

                credentials_per_machine.append(credentials_per_machine_item)

        guest_os_credentials_import_model = cls(
            creds=creds,
            credentials_per_machine=credentials_per_machine,
        )

        guest_os_credentials_import_model.additional_properties = d
        return guest_os_credentials_import_model

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
