from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureMachinesBrowserFilters")


@_attrs_define
class AzureMachinesBrowserFilters:
    """Microsoft Azure machines filters. Using the filters reduces not only the number of records in the response body but
    also the response time.

        Attributes:
            resource_group (str | Unset): Filters compute resources by Microsoft Azure resource group.
            name (str | Unset): Filters compute resources by Microsoft Azure virtual machine name.
    """

    resource_group: str | Unset = UNSET
    name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resource_group = self.resource_group

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if resource_group is not UNSET:
            field_dict["resourceGroup"] = resource_group
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource_group = d.pop("resourceGroup", UNSET)

        name = d.pop("name", UNSET)

        azure_machines_browser_filters = cls(
            resource_group=resource_group,
            name=name,
        )

        azure_machines_browser_filters.additional_properties = d
        return azure_machines_browser_filters

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
