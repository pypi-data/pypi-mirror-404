from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_user_filters_order_column import EUserFiltersOrderColumn
from ..models.e_user_type import EUserType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserFilters")


@_attrs_define
class UserFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EUserFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EUserType] | Unset):
        role_id_filter (UUID | Unset):
        role_name_filter (str | Unset):
        is_service_account_filter (bool | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EUserFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: list[EUserType] | Unset = UNSET
    role_id_filter: UUID | Unset = UNSET
    role_name_filter: str | Unset = UNSET
    is_service_account_filter: bool | Unset = UNSET
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

        role_id_filter: str | Unset = UNSET
        if not isinstance(self.role_id_filter, Unset):
            role_id_filter = str(self.role_id_filter)

        role_name_filter = self.role_name_filter

        is_service_account_filter = self.is_service_account_filter

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
        if role_id_filter is not UNSET:
            field_dict["roleIdFilter"] = role_id_filter
        if role_name_filter is not UNSET:
            field_dict["roleNameFilter"] = role_name_filter
        if is_service_account_filter is not UNSET:
            field_dict["isServiceAccountFilter"] = is_service_account_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EUserFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EUserFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[EUserType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = EUserType(type_filter_item_data)

                type_filter.append(type_filter_item)

        _role_id_filter = d.pop("roleIdFilter", UNSET)
        role_id_filter: UUID | Unset
        if isinstance(_role_id_filter, Unset):
            role_id_filter = UNSET
        else:
            role_id_filter = UUID(_role_id_filter)

        role_name_filter = d.pop("roleNameFilter", UNSET)

        is_service_account_filter = d.pop("isServiceAccountFilter", UNSET)

        user_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            role_id_filter=role_id_filter,
            role_name_filter=role_name_filter,
            is_service_account_filter=is_service_account_filter,
        )

        user_filters.additional_properties = d
        return user_filters

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
