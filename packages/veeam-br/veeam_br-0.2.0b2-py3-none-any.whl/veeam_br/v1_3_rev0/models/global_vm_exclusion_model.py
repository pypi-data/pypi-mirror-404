from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="GlobalVMExclusionModel")


@_attrs_define
class GlobalVMExclusionModel:
    """Global VM exclusion.

    Attributes:
        id (UUID): Global exclusion ID.
        inventory_object (InventoryObjectModel): Inventory object properties.
        note (str | Unset): Note for the global VM exclusion.
    """

    id: UUID
    inventory_object: InventoryObjectModel
    note: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        inventory_object = self.inventory_object.to_dict()

        note = self.note

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "inventoryObject": inventory_object,
            }
        )
        if note is not UNSET:
            field_dict["note"] = note

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        inventory_object = InventoryObjectModel.from_dict(d.pop("inventoryObject"))

        note = d.pop("note", UNSET)

        global_vm_exclusion_model = cls(
            id=id,
            inventory_object=inventory_object,
            note=note,
        )

        global_vm_exclusion_model.additional_properties = d
        return global_vm_exclusion_model

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
