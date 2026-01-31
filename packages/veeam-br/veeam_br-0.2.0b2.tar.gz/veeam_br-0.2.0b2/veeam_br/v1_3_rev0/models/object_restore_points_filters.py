from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_object_restore_points_filters_order_column import EObjectRestorePointsFiltersOrderColumn
from ..models.e_platform_type import EPlatformType
from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectRestorePointsFilters")


@_attrs_define
class ObjectRestorePointsFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EObjectRestorePointsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        backup_id_filter (UUID | Unset):
        backup_object_id_filter (UUID | Unset):
        malware_status_filter (ESuspiciousActivitySeverity | Unset): Malware status.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EObjectRestorePointsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    created_after_filter: datetime.datetime | Unset = UNSET
    created_before_filter: datetime.datetime | Unset = UNSET
    name_filter: str | Unset = UNSET
    platform_name_filter: EPlatformType | Unset = UNSET
    platform_id_filter: UUID | Unset = UNSET
    backup_id_filter: UUID | Unset = UNSET
    backup_object_id_filter: UUID | Unset = UNSET
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        created_after_filter: str | Unset = UNSET
        if not isinstance(self.created_after_filter, Unset):
            created_after_filter = self.created_after_filter.isoformat()

        created_before_filter: str | Unset = UNSET
        if not isinstance(self.created_before_filter, Unset):
            created_before_filter = self.created_before_filter.isoformat()

        name_filter = self.name_filter

        platform_name_filter: str | Unset = UNSET
        if not isinstance(self.platform_name_filter, Unset):
            platform_name_filter = self.platform_name_filter.value

        platform_id_filter: str | Unset = UNSET
        if not isinstance(self.platform_id_filter, Unset):
            platform_id_filter = str(self.platform_id_filter)

        backup_id_filter: str | Unset = UNSET
        if not isinstance(self.backup_id_filter, Unset):
            backup_id_filter = str(self.backup_id_filter)

        backup_object_id_filter: str | Unset = UNSET
        if not isinstance(self.backup_object_id_filter, Unset):
            backup_object_id_filter = str(self.backup_object_id_filter)

        malware_status_filter: str | Unset = UNSET
        if not isinstance(self.malware_status_filter, Unset):
            malware_status_filter = self.malware_status_filter.value

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
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if platform_name_filter is not UNSET:
            field_dict["platformNameFilter"] = platform_name_filter
        if platform_id_filter is not UNSET:
            field_dict["platformIdFilter"] = platform_id_filter
        if backup_id_filter is not UNSET:
            field_dict["backupIdFilter"] = backup_id_filter
        if backup_object_id_filter is not UNSET:
            field_dict["backupObjectIdFilter"] = backup_object_id_filter
        if malware_status_filter is not UNSET:
            field_dict["malwareStatusFilter"] = malware_status_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EObjectRestorePointsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EObjectRestorePointsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _created_after_filter = d.pop("createdAfterFilter", UNSET)
        created_after_filter: datetime.datetime | Unset
        if isinstance(_created_after_filter, Unset):
            created_after_filter = UNSET
        else:
            created_after_filter = isoparse(_created_after_filter)

        _created_before_filter = d.pop("createdBeforeFilter", UNSET)
        created_before_filter: datetime.datetime | Unset
        if isinstance(_created_before_filter, Unset):
            created_before_filter = UNSET
        else:
            created_before_filter = isoparse(_created_before_filter)

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

        _backup_id_filter = d.pop("backupIdFilter", UNSET)
        backup_id_filter: UUID | Unset
        if isinstance(_backup_id_filter, Unset):
            backup_id_filter = UNSET
        else:
            backup_id_filter = UUID(_backup_id_filter)

        _backup_object_id_filter = d.pop("backupObjectIdFilter", UNSET)
        backup_object_id_filter: UUID | Unset
        if isinstance(_backup_object_id_filter, Unset):
            backup_object_id_filter = UNSET
        else:
            backup_object_id_filter = UUID(_backup_object_id_filter)

        _malware_status_filter = d.pop("malwareStatusFilter", UNSET)
        malware_status_filter: ESuspiciousActivitySeverity | Unset
        if isinstance(_malware_status_filter, Unset):
            malware_status_filter = UNSET
        else:
            malware_status_filter = ESuspiciousActivitySeverity(_malware_status_filter)

        object_restore_points_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            name_filter=name_filter,
            platform_name_filter=platform_name_filter,
            platform_id_filter=platform_id_filter,
            backup_id_filter=backup_id_filter,
            backup_object_id_filter=backup_object_id_filter,
            malware_status_filter=malware_status_filter,
        )

        object_restore_points_filters.additional_properties = d
        return object_restore_points_filters

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
