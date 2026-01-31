from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_backup_timeout_type import EAgentBackupTimeoutType

T = TypeVar("T", bound="AgentBackupPolicyBackupTimeoutModel")


@_attrs_define
class AgentBackupPolicyBackupTimeoutModel:
    """Interval between the backup job sessions.

    Attributes:
        type_ (EAgentBackupTimeoutType): Interval between the backup job sessions.
        quantity (int): Number of minutes, hours, or days between the backup job sessions. Specify the interval type in
            the `type` property.
    """

    type_: EAgentBackupTimeoutType
    quantity: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "quantity": quantity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EAgentBackupTimeoutType(d.pop("type"))

        quantity = d.pop("quantity")

        agent_backup_policy_backup_timeout_model = cls(
            type_=type_,
            quantity=quantity,
        )

        agent_backup_policy_backup_timeout_model.additional_properties = d
        return agent_backup_policy_backup_timeout_model

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
