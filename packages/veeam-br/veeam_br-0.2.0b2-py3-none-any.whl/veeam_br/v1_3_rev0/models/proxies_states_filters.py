from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxies_filters_order_column import EProxiesFiltersOrderColumn
from ..models.e_proxy_type import EProxyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProxiesStatesFilters")


@_attrs_define
class ProxiesStatesFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EProxiesFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EProxyType] | Unset):
        host_id_filter (UUID | Unset):
        is_disabled_filter (bool | Unset):
        is_online_filter (bool | Unset):
        is_out_of_date_filter (bool | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EProxiesFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: list[EProxyType] | Unset = UNSET
    host_id_filter: UUID | Unset = UNSET
    is_disabled_filter: bool | Unset = UNSET
    is_online_filter: bool | Unset = UNSET
    is_out_of_date_filter: bool | Unset = UNSET
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

        host_id_filter: str | Unset = UNSET
        if not isinstance(self.host_id_filter, Unset):
            host_id_filter = str(self.host_id_filter)

        is_disabled_filter = self.is_disabled_filter

        is_online_filter = self.is_online_filter

        is_out_of_date_filter = self.is_out_of_date_filter

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
        if host_id_filter is not UNSET:
            field_dict["hostIdFilter"] = host_id_filter
        if is_disabled_filter is not UNSET:
            field_dict["isDisabledFilter"] = is_disabled_filter
        if is_online_filter is not UNSET:
            field_dict["isOnlineFilter"] = is_online_filter
        if is_out_of_date_filter is not UNSET:
            field_dict["isOutOfDateFilter"] = is_out_of_date_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EProxiesFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EProxiesFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[EProxyType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = EProxyType(type_filter_item_data)

                type_filter.append(type_filter_item)

        _host_id_filter = d.pop("hostIdFilter", UNSET)
        host_id_filter: UUID | Unset
        if isinstance(_host_id_filter, Unset):
            host_id_filter = UNSET
        else:
            host_id_filter = UUID(_host_id_filter)

        is_disabled_filter = d.pop("isDisabledFilter", UNSET)

        is_online_filter = d.pop("isOnlineFilter", UNSET)

        is_out_of_date_filter = d.pop("isOutOfDateFilter", UNSET)

        proxies_states_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            host_id_filter=host_id_filter,
            is_disabled_filter=is_disabled_filter,
            is_online_filter=is_online_filter,
            is_out_of_date_filter=is_out_of_date_filter,
        )

        proxies_states_filters.additional_properties = d
        return proxies_states_filters

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
