from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ReplicaMappingRuleModel")


@_attrs_define
class ReplicaMappingRuleModel:
    """Replica mapping rule.

    Attributes:
        original_vm (InventoryObjectModel): Inventory object properties.
        replica_vm (InventoryObjectModel): Inventory object properties.
    """

    original_vm: InventoryObjectModel
    replica_vm: InventoryObjectModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        original_vm = self.original_vm.to_dict()

        replica_vm = self.replica_vm.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "originalVM": original_vm,
                "replicaVM": replica_vm,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        original_vm = InventoryObjectModel.from_dict(d.pop("originalVM"))

        replica_vm = InventoryObjectModel.from_dict(d.pop("replicaVM"))

        replica_mapping_rule_model = cls(
            original_vm=original_vm,
            replica_vm=replica_vm,
        )

        replica_mapping_rule_model.additional_properties = d
        return replica_mapping_rule_model

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
