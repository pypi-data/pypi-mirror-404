from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_hierarchy_type import EHierarchyType
from ..models.e_vmware_inventory_type import EVmwareInventoryType
from ..models.ev_centers_inventory_filters_order_column import EvCentersInventoryFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="VCenterInventoryFilters")


@_attrs_define
class VCenterInventoryFilters:
    """
    Attributes:
        skip (int | Unset): Number of objects to skip.
        limit (int | Unset): Maximum number of objects to return.
        order_column (EvCentersInventoryFiltersOrderColumn | Unset): Sorts vCenter Servers by one of the job parameters.
        order_asc (bool | Unset): If `true`, sorts objects in ascending order by the `orderColumn` parameter.
        object_id_filter (str | Unset): Filters objects by object ID.
        hierarchy_type_filter (EHierarchyType | Unset): VMware vSphere hierarchy type.
        name_filter (str | Unset): Filters objects by the `nameFilter` pattern. The pattern can match any object
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        type_filter (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note that inventory objects
            with multiple tags (*Multitag* type) can only be added in the Veeam Backup & Replication UI or PowerShell.
        parent_container_name_filter (str | Unset): Filters objects by name of the parent container.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    object_id_filter: str | Unset = UNSET
    hierarchy_type_filter: EHierarchyType | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: EVmwareInventoryType | Unset = UNSET
    parent_container_name_filter: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        object_id_filter = self.object_id_filter

        hierarchy_type_filter: str | Unset = UNSET
        if not isinstance(self.hierarchy_type_filter, Unset):
            hierarchy_type_filter = self.hierarchy_type_filter.value

        name_filter = self.name_filter

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        parent_container_name_filter = self.parent_container_name_filter

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit
        if order_column is not UNSET:
            field_dict["orderColumn"] = order_column
        if order_asc is not UNSET:
            field_dict["orderAsc"] = order_asc
        if object_id_filter is not UNSET:
            field_dict["objectIdFilter"] = object_id_filter
        if hierarchy_type_filter is not UNSET:
            field_dict["hierarchyTypeFilter"] = hierarchy_type_filter
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if parent_container_name_filter is not UNSET:
            field_dict["parentContainerNameFilter"] = parent_container_name_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EvCentersInventoryFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EvCentersInventoryFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        object_id_filter = d.pop("objectIdFilter", UNSET)

        _hierarchy_type_filter = d.pop("hierarchyTypeFilter", UNSET)
        hierarchy_type_filter: EHierarchyType | Unset
        if isinstance(_hierarchy_type_filter, Unset):
            hierarchy_type_filter = UNSET
        else:
            hierarchy_type_filter = EHierarchyType(_hierarchy_type_filter)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: EVmwareInventoryType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = EVmwareInventoryType(_type_filter)

        parent_container_name_filter = d.pop("parentContainerNameFilter", UNSET)

        v_center_inventory_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            object_id_filter=object_id_filter,
            hierarchy_type_filter=hierarchy_type_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            parent_container_name_filter=parent_container_name_filter,
        )

        v_center_inventory_filters.additional_properties = d
        return v_center_inventory_filters

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
