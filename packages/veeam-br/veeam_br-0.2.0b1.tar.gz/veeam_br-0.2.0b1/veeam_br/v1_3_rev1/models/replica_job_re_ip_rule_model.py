from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_network_rule_type import ENetworkRuleType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.i_pv_4_network_rule_model import IPv4NetworkRuleModel
    from ..models.i_pv_6_network_rule_model import IPv6NetworkRuleModel


T = TypeVar("T", bound="ReplicaJobReIpRuleModel")


@_attrs_define
class ReplicaJobReIpRuleModel:
    """Re-IP rule.

    Attributes:
        description (str | Unset): Rule description.
        rule_type (ENetworkRuleType | Unset): IP protocol.
        ipv4 (IPv4NetworkRuleModel | Unset): IPv4 network rule.
        ipv6 (IPv6NetworkRuleModel | Unset): IPv6 network rule.
    """

    description: str | Unset = UNSET
    rule_type: ENetworkRuleType | Unset = UNSET
    ipv4: IPv4NetworkRuleModel | Unset = UNSET
    ipv6: IPv6NetworkRuleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        rule_type: str | Unset = UNSET
        if not isinstance(self.rule_type, Unset):
            rule_type = self.rule_type.value

        ipv4: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ipv4, Unset):
            ipv4 = self.ipv4.to_dict()

        ipv6: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ipv6, Unset):
            ipv6 = self.ipv6.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if rule_type is not UNSET:
            field_dict["ruleType"] = rule_type
        if ipv4 is not UNSET:
            field_dict["ipv4"] = ipv4
        if ipv6 is not UNSET:
            field_dict["ipv6"] = ipv6

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.i_pv_4_network_rule_model import IPv4NetworkRuleModel
        from ..models.i_pv_6_network_rule_model import IPv6NetworkRuleModel

        d = dict(src_dict)
        description = d.pop("description", UNSET)

        _rule_type = d.pop("ruleType", UNSET)
        rule_type: ENetworkRuleType | Unset
        if isinstance(_rule_type, Unset):
            rule_type = UNSET
        else:
            rule_type = ENetworkRuleType(_rule_type)

        _ipv4 = d.pop("ipv4", UNSET)
        ipv4: IPv4NetworkRuleModel | Unset
        if isinstance(_ipv4, Unset):
            ipv4 = UNSET
        else:
            ipv4 = IPv4NetworkRuleModel.from_dict(_ipv4)

        _ipv6 = d.pop("ipv6", UNSET)
        ipv6: IPv6NetworkRuleModel | Unset
        if isinstance(_ipv6, Unset):
            ipv6 = UNSET
        else:
            ipv6 = IPv6NetworkRuleModel.from_dict(_ipv6)

        replica_job_re_ip_rule_model = cls(
            description=description,
            rule_type=rule_type,
            ipv4=ipv4,
            ipv6=ipv6,
        )

        replica_job_re_ip_rule_model.additional_properties = d
        return replica_job_re_ip_rule_model

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
