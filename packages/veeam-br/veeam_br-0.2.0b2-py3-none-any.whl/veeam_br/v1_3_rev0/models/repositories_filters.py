from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_filters_order_column import ERepositoryFiltersOrderColumn
from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoriesFilters")


@_attrs_define
class RepositoriesFilters:
    """
    Attributes:
        skip (int | Unset): Number of repositories to skip.
        limit (int | Unset): Maximum number of repositories to return.
        order_column (ERepositoryFiltersOrderColumn | Unset): Sorts repositories by one of the repository parameters.
        order_asc (bool | Unset): If `true`, sorts repositories in the ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters repositories by the `nameFilter` pattern. The pattern can match any
            repository parameter. To substitute one or more characters, use the asterisk (*) character at the beginning
            and/or at the end.
        type_filter (list[ERepositoryType] | Unset):
        host_id_filter (UUID | Unset): Filters repositories by ID of the backup server.
        path_filter (str | Unset): Filters repositories by path to the folder where backup files are stored.
        vmb_api_filter (str | Unset): Filters repositories by VM Backup API parameters converted to the base64 string.
            To obtain the string, call the `GetApiProductInfoString` method of VM Backup API.
        vmb_api_platform (UUID | Unset): Filters repositories by ID of a platform that you use to communicate with VM
            Backup API.
        exclude_extents (bool | Unset): If `true`, filters out repositories that are a part of an extent for Scale-Out
            repositories.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: list[ERepositoryType] | Unset = UNSET
    host_id_filter: UUID | Unset = UNSET
    path_filter: str | Unset = UNSET
    vmb_api_filter: str | Unset = UNSET
    vmb_api_platform: UUID | Unset = UNSET
    exclude_extents: bool | Unset = UNSET
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

        path_filter = self.path_filter

        vmb_api_filter = self.vmb_api_filter

        vmb_api_platform: str | Unset = UNSET
        if not isinstance(self.vmb_api_platform, Unset):
            vmb_api_platform = str(self.vmb_api_platform)

        exclude_extents = self.exclude_extents

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
        if path_filter is not UNSET:
            field_dict["pathFilter"] = path_filter
        if vmb_api_filter is not UNSET:
            field_dict["vmbApiFilter"] = vmb_api_filter
        if vmb_api_platform is not UNSET:
            field_dict["vmbApiPlatform"] = vmb_api_platform
        if exclude_extents is not UNSET:
            field_dict["excludeExtents"] = exclude_extents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ERepositoryFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ERepositoryFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: list[ERepositoryType] | Unset = UNSET
        if _type_filter is not UNSET:
            type_filter = []
            for type_filter_item_data in _type_filter:
                type_filter_item = ERepositoryType(type_filter_item_data)

                type_filter.append(type_filter_item)

        _host_id_filter = d.pop("hostIdFilter", UNSET)
        host_id_filter: UUID | Unset
        if isinstance(_host_id_filter, Unset):
            host_id_filter = UNSET
        else:
            host_id_filter = UUID(_host_id_filter)

        path_filter = d.pop("pathFilter", UNSET)

        vmb_api_filter = d.pop("vmbApiFilter", UNSET)

        _vmb_api_platform = d.pop("vmbApiPlatform", UNSET)
        vmb_api_platform: UUID | Unset
        if isinstance(_vmb_api_platform, Unset):
            vmb_api_platform = UNSET
        else:
            vmb_api_platform = UUID(_vmb_api_platform)

        exclude_extents = d.pop("excludeExtents", UNSET)

        repositories_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            host_id_filter=host_id_filter,
            path_filter=path_filter,
            vmb_api_filter=vmb_api_filter,
            vmb_api_platform=vmb_api_platform,
            exclude_extents=exclude_extents,
        )

        repositories_filters.additional_properties = d
        return repositories_filters

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
