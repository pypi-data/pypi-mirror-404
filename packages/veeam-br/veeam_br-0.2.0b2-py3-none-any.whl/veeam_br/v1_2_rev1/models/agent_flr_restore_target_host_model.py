from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_platform_type import EFlrPlatformType

T = TypeVar("T", bound="AgentFlrRestoreTargetHostModel")


@_attrs_define
class AgentFlrRestoreTargetHostModel:
    """
    Attributes:
        type_ (EFlrPlatformType): Platform type.
        protected_computer_id (UUID): Protected computer ID. To get the ID, use the [Get All Protected
            Computers](#tag/Agents/operation/GetProtectedComputers) request.
    """

    type_: EFlrPlatformType
    protected_computer_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        protected_computer_id = str(self.protected_computer_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "protectedComputerId": protected_computer_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EFlrPlatformType(d.pop("type"))

        protected_computer_id = UUID(d.pop("protectedComputerId"))

        agent_flr_restore_target_host_model = cls(
            type_=type_,
            protected_computer_id=protected_computer_id,
        )

        agent_flr_restore_target_host_model.additional_properties = d
        return agent_flr_restore_target_host_model

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
