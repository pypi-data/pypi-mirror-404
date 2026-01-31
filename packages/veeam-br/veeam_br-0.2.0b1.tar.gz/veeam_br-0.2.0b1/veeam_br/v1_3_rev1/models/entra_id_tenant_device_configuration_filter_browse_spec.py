from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_device_configuration_type import EEntraIdTenantDeviceConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantDeviceConfigurationFilterBrowseSpec")


@_attrs_define
class EntraIdTenantDeviceConfigurationFilterBrowseSpec:
    """
    Attributes:
        display_name (str | Unset):
        description (str | Unset):
        version (int | Unset):
        included_types (list[EEntraIdTenantDeviceConfigurationType] | Unset):
    """

    display_name: str | Unset = UNSET
    description: str | Unset = UNSET
    version: int | Unset = UNSET
    included_types: list[EEntraIdTenantDeviceConfigurationType] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        description = self.description

        version = self.version

        included_types: list[str] | Unset = UNSET
        if not isinstance(self.included_types, Unset):
            included_types = []
            for included_types_item_data in self.included_types:
                included_types_item = included_types_item_data.value
                included_types.append(included_types_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if description is not UNSET:
            field_dict["description"] = description
        if version is not UNSET:
            field_dict["version"] = version
        if included_types is not UNSET:
            field_dict["includedTypes"] = included_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        description = d.pop("description", UNSET)

        version = d.pop("version", UNSET)

        _included_types = d.pop("includedTypes", UNSET)
        included_types: list[EEntraIdTenantDeviceConfigurationType] | Unset = UNSET
        if _included_types is not UNSET:
            included_types = []
            for included_types_item_data in _included_types:
                included_types_item = EEntraIdTenantDeviceConfigurationType(included_types_item_data)

                included_types.append(included_types_item)

        entra_id_tenant_device_configuration_filter_browse_spec = cls(
            display_name=display_name,
            description=description,
            version=version,
            included_types=included_types,
        )

        entra_id_tenant_device_configuration_filter_browse_spec.additional_properties = d
        return entra_id_tenant_device_configuration_filter_browse_spec

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
