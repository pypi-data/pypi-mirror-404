from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protected_computer_type import EProtectedComputerType

if TYPE_CHECKING:
    from ..models.protected_computer_group_model import ProtectedComputerGroupModel


T = TypeVar("T", bound="ProtectedComputerModel")


@_attrs_define
class ProtectedComputerModel:
    """Protected computer.

    Attributes:
        id (UUID): ID of the protected computer.
        name (str): Full DNS name, NetBIOS name or IP address of the protected computer
        type_ (EProtectedComputerType): Type of the protected computer.
        protection_groups (list[ProtectedComputerGroupModel]): Array of protection groups that include the computer.
    """

    id: UUID
    name: str
    type_: EProtectedComputerType
    protection_groups: list[ProtectedComputerGroupModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        protection_groups = []
        for protection_groups_item_data in self.protection_groups:
            protection_groups_item = protection_groups_item_data.to_dict()
            protection_groups.append(protection_groups_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "protectionGroups": protection_groups,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.protected_computer_group_model import ProtectedComputerGroupModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EProtectedComputerType(d.pop("type"))

        protection_groups = []
        _protection_groups = d.pop("protectionGroups")
        for protection_groups_item_data in _protection_groups:
            protection_groups_item = ProtectedComputerGroupModel.from_dict(protection_groups_item_data)

            protection_groups.append(protection_groups_item)

        protected_computer_model = cls(
            id=id,
            name=name,
            type_=type_,
            protection_groups=protection_groups,
        )

        protected_computer_model.additional_properties = d
        return protected_computer_model

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
