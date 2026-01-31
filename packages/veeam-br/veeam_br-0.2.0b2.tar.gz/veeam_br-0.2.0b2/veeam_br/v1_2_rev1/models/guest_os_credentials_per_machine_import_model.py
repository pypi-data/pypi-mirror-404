from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="GuestOsCredentialsPerMachineImportModel")


@_attrs_define
class GuestOsCredentialsPerMachineImportModel:
    """
    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        windows_creds (CredentialsImportModel | Unset): Credentials used for connection.
        linux_creds (CredentialsImportModel | Unset): Credentials used for connection.
    """

    vm_object: InventoryObjectModel
    windows_creds: CredentialsImportModel | Unset = UNSET
    linux_creds: CredentialsImportModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        windows_creds: dict[str, Any] | Unset = UNSET
        if not isinstance(self.windows_creds, Unset):
            windows_creds = self.windows_creds.to_dict()

        linux_creds: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux_creds, Unset):
            linux_creds = self.linux_creds.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if windows_creds is not UNSET:
            field_dict["windowsCreds"] = windows_creds
        if linux_creds is not UNSET:
            field_dict["linuxCreds"] = linux_creds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        _windows_creds = d.pop("windowsCreds", UNSET)
        windows_creds: CredentialsImportModel | Unset
        if isinstance(_windows_creds, Unset):
            windows_creds = UNSET
        else:
            windows_creds = CredentialsImportModel.from_dict(_windows_creds)

        _linux_creds = d.pop("linuxCreds", UNSET)
        linux_creds: CredentialsImportModel | Unset
        if isinstance(_linux_creds, Unset):
            linux_creds = UNSET
        else:
            linux_creds = CredentialsImportModel.from_dict(_linux_creds)

        guest_os_credentials_per_machine_import_model = cls(
            vm_object=vm_object,
            windows_creds=windows_creds,
            linux_creds=linux_creds,
        )

        guest_os_credentials_per_machine_import_model.additional_properties = d
        return guest_os_credentials_per_machine_import_model

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
