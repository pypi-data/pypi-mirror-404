from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.individual_computer_container_model import IndividualComputerContainerModel
    from ..models.protection_group_options_model import ProtectionGroupOptionsModel


T = TypeVar("T", bound="IndividualComputersProtectionGroupModel")


@_attrs_define
class IndividualComputersProtectionGroupModel:
    """Protection group for individual computers.

    Attributes:
        id (UUID): Protection group ID.
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        is_disabled (bool): If `true`, the protection group is disabled
        computers (list[IndividualComputerContainerModel] | Unset): Array of protected computers.
        options (ProtectionGroupOptionsModel | Unset): Protection group options.
    """

    id: UUID
    name: str
    description: str
    type_: EProtectionGroupType
    is_disabled: bool
    computers: list[IndividualComputerContainerModel] | Unset = UNSET
    options: ProtectionGroupOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        is_disabled = self.is_disabled

        computers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.computers, Unset):
            computers = []
            for computers_item_data in self.computers:
                computers_item = computers_item_data.to_dict()
                computers.append(computers_item)

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "isDisabled": is_disabled,
            }
        )
        if computers is not UNSET:
            field_dict["computers"] = computers
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.individual_computer_container_model import IndividualComputerContainerModel
        from ..models.protection_group_options_model import ProtectionGroupOptionsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        _computers = d.pop("computers", UNSET)
        computers: list[IndividualComputerContainerModel] | Unset = UNSET
        if _computers is not UNSET:
            computers = []
            for computers_item_data in _computers:
                computers_item = IndividualComputerContainerModel.from_dict(computers_item_data)

                computers.append(computers_item)

        _options = d.pop("options", UNSET)
        options: ProtectionGroupOptionsModel | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProtectionGroupOptionsModel.from_dict(_options)

        individual_computers_protection_group_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            is_disabled=is_disabled,
            computers=computers,
            options=options,
        )

        individual_computers_protection_group_model.additional_properties = d
        return individual_computers_protection_group_model

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
