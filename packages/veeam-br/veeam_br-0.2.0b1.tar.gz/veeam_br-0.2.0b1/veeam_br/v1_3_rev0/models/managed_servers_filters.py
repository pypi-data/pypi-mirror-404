from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_host_updates_state import EHostUpdatesState
from ..models.e_managed_server_state import EManagedServerState
from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_filters_order_column import EManagedServersFiltersOrderColumn
from ..models.e_vi_host_type import EViHostType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ManagedServersFilters")


@_attrs_define
class ManagedServersFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EManagedServersFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EManagedServerType] | Unset):
        vi_type_filter (EViHostType | Unset): Type of the VMware vSphere server.
        server_state_filter (EManagedServerState | Unset): Managed server state.
        updates_state_filter (list[EHostUpdatesState] | Unset):
        include_nested_hosts (bool | Unset): If `true`, nested hosts (where the hypervisor is running inside a VM) are
            included in the selection. Default: False.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: list[EManagedServerType] | Unset = UNSET
    vi_type_filter: EViHostType | Unset = UNSET
    server_state_filter: EManagedServerState | Unset = UNSET
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET
    include_nested_hosts: bool | Unset = False
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

        vi_type_filter: str | Unset = UNSET
        if not isinstance(self.vi_type_filter, Unset):
            vi_type_filter = self.vi_type_filter.value

        server_state_filter: str | Unset = UNSET
        if not isinstance(self.server_state_filter, Unset):
            server_state_filter = self.server_state_filter.value

        updates_state_filter: list[str] | Unset = UNSET
        if not isinstance(self.updates_state_filter, Unset):
            updates_state_filter = []
            for updates_state_filter_item_data in self.updates_state_filter:
                updates_state_filter_item = updates_state_filter_item_data.value
                updates_state_filter.append(updates_state_filter_item)

        include_nested_hosts = self.include_nested_hosts

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
        if vi_type_filter is not UNSET:
            field_dict["viTypeFilter"] = vi_type_filter
        if server_state_filter is not UNSET:
            field_dict["serverStateFilter"] = server_state_filter
        if updates_state_filter is not UNSET:
            field_dict["updatesStateFilter"] = updates_state_filter
        if include_nested_hosts is not UNSET:
            field_dict["includeNestedHosts"] = include_nested_hosts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EManagedServersFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EManagedServersFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[EManagedServerType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = EManagedServerType(type_filter_item_data)

                type_filter.append(type_filter_item)

        _vi_type_filter = d.pop("viTypeFilter", UNSET)
        vi_type_filter: EViHostType | Unset
        if isinstance(_vi_type_filter, Unset):
            vi_type_filter = UNSET
        else:
            vi_type_filter = EViHostType(_vi_type_filter)

        _server_state_filter = d.pop("serverStateFilter", UNSET)
        server_state_filter: EManagedServerState | Unset
        if isinstance(_server_state_filter, Unset):
            server_state_filter = UNSET
        else:
            server_state_filter = EManagedServerState(_server_state_filter)

        _updates_state_filter = d.pop("updatesStateFilter", UNSET)
        updates_state_filter: list[EHostUpdatesState] | Unset = UNSET
        if _updates_state_filter is not UNSET:
            updates_state_filter = []
            for updates_state_filter_item_data in _updates_state_filter:
                updates_state_filter_item = EHostUpdatesState(updates_state_filter_item_data)

                updates_state_filter.append(updates_state_filter_item)

        include_nested_hosts = d.pop("includeNestedHosts", UNSET)

        managed_servers_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            vi_type_filter=vi_type_filter,
            server_state_filter=server_state_filter,
            updates_state_filter=updates_state_filter,
            include_nested_hosts=include_nested_hosts,
        )

        managed_servers_filters.additional_properties = d
        return managed_servers_filters

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
