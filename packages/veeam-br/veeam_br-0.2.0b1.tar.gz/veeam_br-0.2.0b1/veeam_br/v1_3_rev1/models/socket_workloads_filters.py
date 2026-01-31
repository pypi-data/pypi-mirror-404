from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_socket_license_object_type import ESocketLicenseObjectType
from ..models.e_socket_workloads_filters_order_column import ESocketWorkloadsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="SocketWorkloadsFilters")


@_attrs_define
class SocketWorkloadsFilters:
    """
    Attributes:
        skip (int | Unset): Number of workloads to skip.
        limit (int | Unset): Maximum number of results to return.
        order_column (ESocketWorkloadsFiltersOrderColumn | Unset): Sorts licensed hosts according to one of the
            parameters.
        order_asc (bool | Unset): If `true`, sorts workloads in ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters workloads by the `nameFilter` pattern. The pattern can match any workload
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        host_name_filter (str | Unset): Filters workloads by hostname.
        host_id_filter (UUID | Unset): Filters workloads by host ID.
        sockets_number_filter (int | Unset): Filters workloads by the number of sockets they use.
        cores_number_filter (int | Unset): Filters workloads by the number of CPU cores they use.
        type_filter (ESocketLicenseObjectType | Unset): Type of host covered by socket license.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ESocketWorkloadsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    host_name_filter: str | Unset = UNSET
    host_id_filter: UUID | Unset = UNSET
    sockets_number_filter: int | Unset = UNSET
    cores_number_filter: int | Unset = UNSET
    type_filter: ESocketLicenseObjectType | Unset = UNSET
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

        host_id_filter: str | Unset = UNSET
        if not isinstance(self.host_id_filter, Unset):
            host_id_filter = str(self.host_id_filter)

        sockets_number_filter = self.sockets_number_filter

        cores_number_filter = self.cores_number_filter

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
        if host_name_filter is not UNSET:
            field_dict["hostNameFilter"] = host_name_filter
        if host_id_filter is not UNSET:
            field_dict["hostIdFilter"] = host_id_filter
        if sockets_number_filter is not UNSET:
            field_dict["socketsNumberFilter"] = sockets_number_filter
        if cores_number_filter is not UNSET:
            field_dict["coresNumberFilter"] = cores_number_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ESocketWorkloadsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ESocketWorkloadsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        host_name_filter = d.pop("hostNameFilter", UNSET)

        _host_id_filter = d.pop("hostIdFilter", UNSET)
        host_id_filter: UUID | Unset
        if isinstance(_host_id_filter, Unset):
            host_id_filter = UNSET
        else:
            host_id_filter = UUID(_host_id_filter)

        sockets_number_filter = d.pop("socketsNumberFilter", UNSET)

        cores_number_filter = d.pop("coresNumberFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: ESocketLicenseObjectType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = ESocketLicenseObjectType(_type_filter)

        socket_workloads_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            host_name_filter=host_name_filter,
            host_id_filter=host_id_filter,
            sockets_number_filter=sockets_number_filter,
            cores_number_filter=cores_number_filter,
            type_filter=type_filter,
        )

        socket_workloads_filters.additional_properties = d
        return socket_workloads_filters

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
