from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_admin_unit_visibility_type import EEntraIdTenantAdminUnitVisibilityType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantAdminUnitFilterBrowseSpec")


@_attrs_define
class EntraIdTenantAdminUnitFilterBrowseSpec:
    """Filtering options.

    Attributes:
        display_name (str | Unset): Administrative unit diplay name.
        visibilities (list[EEntraIdTenantAdminUnitVisibilityType] | Unset): Array of visibility options.
    """

    display_name: str | Unset = UNSET
    visibilities: list[EEntraIdTenantAdminUnitVisibilityType] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        visibilities: list[str] | Unset = UNSET
        if not isinstance(self.visibilities, Unset):
            visibilities = []
            for visibilities_item_data in self.visibilities:
                visibilities_item = visibilities_item_data.value
                visibilities.append(visibilities_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if visibilities is not UNSET:
            field_dict["visibilities"] = visibilities

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        _visibilities = d.pop("visibilities", UNSET)
        visibilities: list[EEntraIdTenantAdminUnitVisibilityType] | Unset = UNSET
        if _visibilities is not UNSET:
            visibilities = []
            for visibilities_item_data in _visibilities:
                visibilities_item = EEntraIdTenantAdminUnitVisibilityType(visibilities_item_data)

                visibilities.append(visibilities_item)

        entra_id_tenant_admin_unit_filter_browse_spec = cls(
            display_name=display_name,
            visibilities=visibilities,
        )

        entra_id_tenant_admin_unit_filter_browse_spec.additional_properties = d
        return entra_id_tenant_admin_unit_filter_browse_spec

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
