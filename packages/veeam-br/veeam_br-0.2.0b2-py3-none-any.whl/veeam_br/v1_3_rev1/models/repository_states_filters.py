from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_states_filters_order_column import ERepositoryStatesFiltersOrderColumn
from ..models.e_repository_type import ERepositoryType
from ..models.e_scale_out_repository_extent_type import EScaleOutRepositoryExtentType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryStatesFilters")


@_attrs_define
class RepositoryStatesFilters:
    """Filters repositories by the specified parameters.

    Attributes:
        skip (int | Unset): Skips the specified number of repositories.
        limit (int | Unset): Returns the specified number of repositories.
        order_column (ERepositoryStatesFiltersOrderColumn | Unset): Orders repositories by the specified column.
        order_asc (bool | Unset): If `true`, sorts repositories in ascending order by the `orderColumn` parameter.
        id_filter (UUID | Unset):
        name_filter (str | Unset): Filters repositories by the `nameFilter` pattern. The pattern can match any
            repository parameter. To substitute one or more characters, use the asterisk (*) character at the beginning
            and/or at the end.
        type_filter (ERepositoryType | Unset): Repository type.
        capacity_filter (float | Unset): Filters repositories by repository capacity.
        free_space_filter (float | Unset): Filters repositories by repository free space.
        used_space_filter (float | Unset): Filters repositories by repository used space.
        is_online_filter (bool | Unset): Filters repositories by repository connection status.
        is_out_of_date_filter (bool | Unset): Filters repositories by repository components status.
        sobr_id_filter (UUID | Unset):
        sobr_extent_type_filter (list[EScaleOutRepositoryExtentType] | Unset):
        sobr_membership_filter (str | Unset):
        exclude_extents (bool | Unset): If `true`, filters out repositories that are a part of an extent for Scale-Out
            repositories.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    id_filter: UUID | Unset = UNSET
    name_filter: str | Unset = UNSET
    type_filter: ERepositoryType | Unset = UNSET
    capacity_filter: float | Unset = UNSET
    free_space_filter: float | Unset = UNSET
    used_space_filter: float | Unset = UNSET
    is_online_filter: bool | Unset = UNSET
    is_out_of_date_filter: bool | Unset = UNSET
    sobr_id_filter: UUID | Unset = UNSET
    sobr_extent_type_filter: list[EScaleOutRepositoryExtentType] | Unset = UNSET
    sobr_membership_filter: str | Unset = UNSET
    exclude_extents: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        id_filter: str | Unset = UNSET
        if not isinstance(self.id_filter, Unset):
            id_filter = str(self.id_filter)

        name_filter = self.name_filter

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        capacity_filter = self.capacity_filter

        free_space_filter = self.free_space_filter

        used_space_filter = self.used_space_filter

        is_online_filter = self.is_online_filter

        is_out_of_date_filter = self.is_out_of_date_filter

        sobr_id_filter: str | Unset = UNSET
        if not isinstance(self.sobr_id_filter, Unset):
            sobr_id_filter = str(self.sobr_id_filter)

        sobr_extent_type_filter: list[str] | Unset = UNSET
        if not isinstance(self.sobr_extent_type_filter, Unset):
            sobr_extent_type_filter = []
            for sobr_extent_type_filter_item_data in self.sobr_extent_type_filter:
                sobr_extent_type_filter_item = sobr_extent_type_filter_item_data.value
                sobr_extent_type_filter.append(sobr_extent_type_filter_item)

        sobr_membership_filter = self.sobr_membership_filter

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
        if id_filter is not UNSET:
            field_dict["idFilter"] = id_filter
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if capacity_filter is not UNSET:
            field_dict["capacityFilter"] = capacity_filter
        if free_space_filter is not UNSET:
            field_dict["freeSpaceFilter"] = free_space_filter
        if used_space_filter is not UNSET:
            field_dict["usedSpaceFilter"] = used_space_filter
        if is_online_filter is not UNSET:
            field_dict["isOnlineFilter"] = is_online_filter
        if is_out_of_date_filter is not UNSET:
            field_dict["isOutOfDateFilter"] = is_out_of_date_filter
        if sobr_id_filter is not UNSET:
            field_dict["sobrIdFilter"] = sobr_id_filter
        if sobr_extent_type_filter is not UNSET:
            field_dict["sobrExtentTypeFilter"] = sobr_extent_type_filter
        if sobr_membership_filter is not UNSET:
            field_dict["sobrMembershipFilter"] = sobr_membership_filter
        if exclude_extents is not UNSET:
            field_dict["excludeExtents"] = exclude_extents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ERepositoryStatesFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ERepositoryStatesFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _id_filter = d.pop("idFilter", UNSET)
        id_filter: UUID | Unset
        if isinstance(_id_filter, Unset):
            id_filter = UNSET
        else:
            id_filter = UUID(_id_filter)

        name_filter = d.pop("nameFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: ERepositoryType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = ERepositoryType(_type_filter)

        capacity_filter = d.pop("capacityFilter", UNSET)

        free_space_filter = d.pop("freeSpaceFilter", UNSET)

        used_space_filter = d.pop("usedSpaceFilter", UNSET)

        is_online_filter = d.pop("isOnlineFilter", UNSET)

        is_out_of_date_filter = d.pop("isOutOfDateFilter", UNSET)

        _sobr_id_filter = d.pop("sobrIdFilter", UNSET)
        sobr_id_filter: UUID | Unset
        if isinstance(_sobr_id_filter, Unset):
            sobr_id_filter = UNSET
        else:
            sobr_id_filter = UUID(_sobr_id_filter)

        _sobr_extent_type_filter = d.pop("sobrExtentTypeFilter", UNSET)
        sobr_extent_type_filter: list[EScaleOutRepositoryExtentType] | Unset = UNSET
        if _sobr_extent_type_filter is not UNSET:
            sobr_extent_type_filter = []
            for sobr_extent_type_filter_item_data in _sobr_extent_type_filter:
                sobr_extent_type_filter_item = EScaleOutRepositoryExtentType(sobr_extent_type_filter_item_data)

                sobr_extent_type_filter.append(sobr_extent_type_filter_item)

        sobr_membership_filter = d.pop("sobrMembershipFilter", UNSET)

        exclude_extents = d.pop("excludeExtents", UNSET)

        repository_states_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            id_filter=id_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            capacity_filter=capacity_filter,
            free_space_filter=free_space_filter,
            used_space_filter=used_space_filter,
            is_online_filter=is_online_filter,
            is_out_of_date_filter=is_out_of_date_filter,
            sobr_id_filter=sobr_id_filter,
            sobr_extent_type_filter=sobr_extent_type_filter,
            sobr_membership_filter=sobr_membership_filter,
            exclude_extents=exclude_extents,
        )

        repository_states_filters.additional_properties = d
        return repository_states_filters

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
