from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instance_workloads_filters_order_column import EInstanceWorkloadsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceWorkloadsFilters")


@_attrs_define
class InstanceWorkloadsFilters:
    """
    Attributes:
        skip (int | Unset): Number of workloads to skip.
        limit (int | Unset): Maximum number of workloads to return.
        order_column (EInstanceWorkloadsFiltersOrderColumn | Unset): Sorts licensed workloads according to one of the
            parameters.
        order_asc (bool | Unset): If `true`, sorts workloads in the ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters workloads by the `nameFilter` pattern. The pattern can match any session
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        host_name_filter (str | Unset): Filters workloads by hostname.
        used_instances_number_filter (float | Unset): Filters workloads by the number of consumed instances.
        type_filter (str | Unset): Filters workloads by workload type.
        instance_id_filter (UUID | Unset): Filters workloads by instance ID.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EInstanceWorkloadsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    host_name_filter: str | Unset = UNSET
    used_instances_number_filter: float | Unset = UNSET
    type_filter: str | Unset = UNSET
    instance_id_filter: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        host_name_filter = self.host_name_filter

        used_instances_number_filter = self.used_instances_number_filter

        type_filter = self.type_filter

        instance_id_filter: str | Unset = UNSET
        if not isinstance(self.instance_id_filter, Unset):
            instance_id_filter = str(self.instance_id_filter)

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
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if host_name_filter is not UNSET:
            field_dict["hostNameFilter"] = host_name_filter
        if used_instances_number_filter is not UNSET:
            field_dict["usedInstancesNumberFilter"] = used_instances_number_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if instance_id_filter is not UNSET:
            field_dict["instanceIdFilter"] = instance_id_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EInstanceWorkloadsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EInstanceWorkloadsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        host_name_filter = d.pop("hostNameFilter", UNSET)

        used_instances_number_filter = d.pop("usedInstancesNumberFilter", UNSET)

        type_filter = d.pop("typeFilter", UNSET)

        _instance_id_filter = d.pop("instanceIdFilter", UNSET)
        instance_id_filter: UUID | Unset
        if isinstance(_instance_id_filter, Unset):
            instance_id_filter = UNSET
        else:
            instance_id_filter = UUID(_instance_id_filter)

        instance_workloads_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            host_name_filter=host_name_filter,
            used_instances_number_filter=used_instances_number_filter,
            type_filter=type_filter,
            instance_id_filter=instance_id_filter,
        )

        instance_workloads_filters.additional_properties = d
        return instance_workloads_filters

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
