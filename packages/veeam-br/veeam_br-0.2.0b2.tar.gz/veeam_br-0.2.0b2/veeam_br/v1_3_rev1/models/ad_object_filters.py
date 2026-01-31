from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ead_object_filters_order_column import EADObjectFiltersOrderColumn
from ..models.ead_object_type import EADObjectType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ADObjectFilters")


@_attrs_define
class ADObjectFilters:
    """
    Attributes:
        skip (int | Unset): Number of Active Directory objects to skip.
        limit (int | Unset): Maximum number of Active Directory objects to return.
        order_column (EADObjectFiltersOrderColumn | Unset): Sorts Active Directory objects by one of the parameters.
        order_asc (bool | Unset): Sorts Active Directory objects in ascending order by the `orderColumn` parameter.
        full_name_filter (str | Unset): Filters Active Directory objects by the `fullNameFilter` pattern. The pattern
            can match any Active Directory object parameter. To substitute one or more characters, use the asterisk (*)
            character at the beginning and/or at the end.
        type_filter (EADObjectType | Unset): Type of Active Directory object.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EADObjectFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    full_name_filter: str | Unset = UNSET
    type_filter: EADObjectType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        full_name_filter = self.full_name_filter

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

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
        if full_name_filter is not UNSET:
            field_dict["fullNameFilter"] = full_name_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EADObjectFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EADObjectFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        full_name_filter = d.pop("fullNameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: EADObjectType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = EADObjectType(_type_filter)

        ad_object_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            full_name_filter=full_name_filter,
            type_filter=type_filter,
        )

        ad_object_filters.additional_properties = d
        return ad_object_filters

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
