from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_backup_policy_destination_type import EAgentBackupPolicyDestinationType

T = TypeVar("T", bound="AgentBackupPolicyDestinationModel")


@_attrs_define
class AgentBackupPolicyDestinationModel:
    """Settings for destination of Veeam Agent backup policy.

    Attributes:
        destination_type (EAgentBackupPolicyDestinationType): Destination type for Veeam Agent backup policy.
    """

    destination_type: EAgentBackupPolicyDestinationType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        destination_type = self.destination_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "destinationType": destination_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        destination_type = EAgentBackupPolicyDestinationType(d.pop("destinationType"))

        agent_backup_policy_destination_model = cls(
            destination_type=destination_type,
        )

        agent_backup_policy_destination_model.additional_properties = d
        return agent_backup_policy_destination_model

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
