from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..models.e_unstructured_data_servers_filters_order_column import EUnstructuredDataServersFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataServersFilters")


@_attrs_define
class UnstructuredDataServersFilters:
    """
    Attributes:
        skip (int | Unset): Number of unstructured data servers to skip.
        limit (int | Unset): Maximum number of unstructured data servers to return.
        order_column (EUnstructuredDataServersFiltersOrderColumn | Unset): Sorts unstructured data servers by one of the
            unstructured data server parameters.
        order_asc (bool | Unset): If `true`, sorts unstructured data servers in ascending order by the `orderColumn`
            parameter.
        name_filter (str | Unset): Filters unstructured data servers by name. To substitute one or more characters, use
            the asterisk (*) character at the beginning, at the end or both.
        type_filter (list[EUnstructuredDataServerType] | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EUnstructuredDataServersFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: list[EUnstructuredDataServerType] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        type_filter: list[str] | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = []
            for type_filter_item_data in self.type_filter:
                type_filter_item = type_filter_item_data.value
                type_filter.append(type_filter_item)

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
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EUnstructuredDataServersFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EUnstructuredDataServersFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[EUnstructuredDataServerType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = EUnstructuredDataServerType(type_filter_item_data)

                type_filter.append(type_filter_item)

        unstructured_data_servers_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
        )

        unstructured_data_servers_filters.additional_properties = d
        return unstructured_data_servers_filters

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
