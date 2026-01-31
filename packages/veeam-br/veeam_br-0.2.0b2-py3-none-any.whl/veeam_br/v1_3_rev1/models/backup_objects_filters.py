from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_objects_filters_order_column import EBackupObjectsFiltersOrderColumn
from ..models.e_platform_type import EPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupObjectsFilters")


@_attrs_define
class BackupObjectsFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupObjectsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        type_filter (str | Unset):
        vi_type_filter (str | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    platform_name_filter: EPlatformType | Unset = UNSET
    platform_id_filter: UUID | Unset = UNSET
    type_filter: str | Unset = UNSET
    vi_type_filter: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        platform_name_filter: str | Unset = UNSET
        if not isinstance(self.platform_name_filter, Unset):
            platform_name_filter = self.platform_name_filter.value

        platform_id_filter: str | Unset = UNSET
        if not isinstance(self.platform_id_filter, Unset):
            platform_id_filter = str(self.platform_id_filter)

        type_filter = self.type_filter

        vi_type_filter = self.vi_type_filter

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
        if platform_name_filter is not UNSET:
            field_dict["platformNameFilter"] = platform_name_filter
        if platform_id_filter is not UNSET:
            field_dict["platformIdFilter"] = platform_id_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if vi_type_filter is not UNSET:
            field_dict["viTypeFilter"] = vi_type_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EBackupObjectsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EBackupObjectsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _platform_name_filter = d.pop("platformNameFilter", UNSET)
        platform_name_filter: EPlatformType | Unset
        if isinstance(_platform_name_filter, Unset):
            platform_name_filter = UNSET
        else:
            platform_name_filter = EPlatformType(_platform_name_filter)

        _platform_id_filter = d.pop("platformIdFilter", UNSET)
        platform_id_filter: UUID | Unset
        if isinstance(_platform_id_filter, Unset):
            platform_id_filter = UNSET
        else:
            platform_id_filter = UUID(_platform_id_filter)

        type_filter = d.pop("typeFilter", UNSET)

        vi_type_filter = d.pop("viTypeFilter", UNSET)

        backup_objects_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            platform_name_filter=platform_name_filter,
            platform_id_filter=platform_id_filter,
            type_filter=type_filter,
            vi_type_filter=vi_type_filter,
        )

        backup_objects_filters.additional_properties = d
        return backup_objects_filters

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
