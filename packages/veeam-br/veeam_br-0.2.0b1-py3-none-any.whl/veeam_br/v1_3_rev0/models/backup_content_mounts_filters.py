from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_content_disk_publish_mode import EBackupContentDiskPublishMode
from ..models.e_backup_content_mount_state import EBackupContentMountState
from ..models.e_backup_content_mounts_filters_order_column import EBackupContentMountsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupContentMountsFilters")


@_attrs_define
class BackupContentMountsFilters:
    """
    Attributes:
        skip (int | Unset): Number of mount points to skip.
        limit (int | Unset): Maximum number of mount points to return.
        order_column (EBackupContentMountsFiltersOrderColumn | Unset): Sorts mount points by one of the mount point
            parameters.
        order_asc (bool | Unset): If `true`, sorts mount points in the ascending order by the `orderColumn` parameter.
        state_filter (EBackupContentMountState | Unset): Mount state.
        mode_filter (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    state_filter: EBackupContentMountState | Unset = UNSET
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        state_filter: str | Unset = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

        mode_filter: str | Unset = UNSET
        if not isinstance(self.mode_filter, Unset):
            mode_filter = self.mode_filter.value

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
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if mode_filter is not UNSET:
            field_dict["modeFilter"] = mode_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EBackupContentMountsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EBackupContentMountsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: EBackupContentMountState | Unset
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = EBackupContentMountState(_state_filter)

        _mode_filter = d.pop("modeFilter", UNSET)
        mode_filter: EBackupContentDiskPublishMode | Unset
        if isinstance(_mode_filter, Unset):
            mode_filter = UNSET
        else:
            mode_filter = EBackupContentDiskPublishMode(_mode_filter)

        backup_content_mounts_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            state_filter=state_filter,
            mode_filter=mode_filter,
        )

        backup_content_mounts_filters.additional_properties = d
        return backup_content_mounts_filters

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
