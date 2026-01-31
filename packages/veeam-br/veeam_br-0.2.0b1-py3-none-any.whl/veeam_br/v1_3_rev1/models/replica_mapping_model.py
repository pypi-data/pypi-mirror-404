from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.replica_mapping_rule_model import ReplicaMappingRuleModel


T = TypeVar("T", bound="ReplicaMappingModel")


@_attrs_define
class ReplicaMappingModel:
    """Replica mapping settings. This option can be used if you already have ready-to-use copies of the source VMs in the
    target site.

        Attributes:
            is_enabled (bool): If `true`, replica mapping is enabled.
            mapping_rules (list[ReplicaMappingRuleModel] | Unset): Array of mapping rules for replicas.<ul><li>`originalVM`
                — source VM</li><li>`replicaVM` — ready-to-use copy of this VM in the target site</li></ul>
    """

    is_enabled: bool
    mapping_rules: list[ReplicaMappingRuleModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        mapping_rules: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.mapping_rules, Unset):
            mapping_rules = []
            for mapping_rules_item_data in self.mapping_rules:
                mapping_rules_item = mapping_rules_item_data.to_dict()
                mapping_rules.append(mapping_rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if mapping_rules is not UNSET:
            field_dict["mappingRules"] = mapping_rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.replica_mapping_rule_model import ReplicaMappingRuleModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _mapping_rules = d.pop("mappingRules", UNSET)
        mapping_rules: list[ReplicaMappingRuleModel] | Unset = UNSET
        if _mapping_rules is not UNSET:
            mapping_rules = []
            for mapping_rules_item_data in _mapping_rules:
                mapping_rules_item = ReplicaMappingRuleModel.from_dict(mapping_rules_item_data)

                mapping_rules.append(mapping_rules_item)

        replica_mapping_model = cls(
            is_enabled=is_enabled,
            mapping_rules=mapping_rules,
        )

        replica_mapping_model.additional_properties = d
        return replica_mapping_model

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
