from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeResourceGroupModel")


@_attrs_define
class AzureComputeResourceGroupModel:
    """Microsoft Azure resource group.

    Attributes:
        resource_group (str | Unset): Resource group name.
        new_resource_group_name (str | Unset): New resource group name.
    """

    resource_group: str | Unset = UNSET
    new_resource_group_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_group = self.resource_group

        new_resource_group_name = self.new_resource_group_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if resource_group is not UNSET:
            field_dict["resourceGroup"] = resource_group
        if new_resource_group_name is not UNSET:
            field_dict["newResourceGroupName"] = new_resource_group_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource_group = d.pop("resourceGroup", UNSET)

        new_resource_group_name = d.pop("newResourceGroupName", UNSET)

        azure_compute_resource_group_model = cls(
            resource_group=resource_group,
            new_resource_group_name=new_resource_group_name,
        )

        azure_compute_resource_group_model.additional_properties = d
        return azure_compute_resource_group_model

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
