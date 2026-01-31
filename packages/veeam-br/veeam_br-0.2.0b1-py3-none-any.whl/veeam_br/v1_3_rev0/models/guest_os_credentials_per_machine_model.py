from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="GuestOsCredentialsPerMachineModel")


@_attrs_define
class GuestOsCredentialsPerMachineModel:
    """Settings for per-machine guest OS credentials.

    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        credentials_id (UUID | Unset): Credentials ID.
        credentials_type (ECredentialsType | Unset): Credentials type.
        default (bool | Unset): If `true`, Veeam Backup & Replication will use job-level credentials.
    """

    vm_object: InventoryObjectModel
    credentials_id: UUID | Unset = UNSET
    credentials_type: ECredentialsType | Unset = UNSET
    default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        credentials_type: str | Unset = UNSET
        if not isinstance(self.credentials_type, Unset):
            credentials_type = self.credentials_type.value

        default = self.default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if credentials_type is not UNSET:
            field_dict["credentialsType"] = credentials_type
        if default is not UNSET:
            field_dict["default"] = default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _credentials_type = d.pop("credentialsType", UNSET)
        credentials_type: ECredentialsType | Unset
        if isinstance(_credentials_type, Unset):
            credentials_type = UNSET
        else:
            credentials_type = ECredentialsType(_credentials_type)

        default = d.pop("default", UNSET)

        guest_os_credentials_per_machine_model = cls(
            vm_object=vm_object,
            credentials_id=credentials_id,
            credentials_type=credentials_type,
            default=default,
        )

        guest_os_credentials_per_machine_model.additional_properties = d
        return guest_os_credentials_per_machine_model

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
