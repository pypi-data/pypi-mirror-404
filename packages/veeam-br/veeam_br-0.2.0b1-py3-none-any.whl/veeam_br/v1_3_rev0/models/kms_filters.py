from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_key_management_server_type import EKeyManagementServerType
from ..models.ekms_filters_order_column import EKMSFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="KMSFilters")


@_attrs_define
class KMSFilters:
    """
    Attributes:
        skip (int | Unset): Number of KMS servers to skip.
        limit (int | Unset): Maximum number of KMS servers to return.
        order_column (EKMSFiltersOrderColumn | Unset):
        order_asc (bool | Unset): If `true`, sorts KMS servers in the ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters KMS servers by the `nameFilter` pattern. The pattern can match any KMS server
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        type_filter (EKeyManagementServerType | Unset): KMS server type.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EKMSFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: EKeyManagementServerType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

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
        order_column: EKMSFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EKMSFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: EKeyManagementServerType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = EKeyManagementServerType(_type_filter)

        kms_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
        )

        kms_filters.additional_properties = d
        return kms_filters

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
