from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_flr_audit_items_filters_order_column import EFlrAuditItemsFiltersOrderColumn
from ..models.e_flr_item_restore_status import EFlrItemRestoreStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrAuditItemsFilters")


@_attrs_define
class FlrAuditItemsFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EFlrAuditItemsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        restore_status_filter (list[EFlrItemRestoreStatus] | Unset):
        restore_ended_before_filter (datetime.datetime | Unset):
        restore_ended_after_filter (datetime.datetime | Unset):
        initiator_name_filter (str | Unset):
        name_filter (str | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EFlrAuditItemsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    restore_status_filter: list[EFlrItemRestoreStatus] | Unset = UNSET
    restore_ended_before_filter: datetime.datetime | Unset = UNSET
    restore_ended_after_filter: datetime.datetime | Unset = UNSET
    initiator_name_filter: str | Unset = UNSET
    name_filter: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        restore_status_filter: list[str] | Unset = UNSET
        if not isinstance(self.restore_status_filter, Unset):
            restore_status_filter = []
            for restore_status_filter_item_data in self.restore_status_filter:
                restore_status_filter_item = restore_status_filter_item_data.value
                restore_status_filter.append(restore_status_filter_item)

        restore_ended_before_filter: str | Unset = UNSET
        if not isinstance(self.restore_ended_before_filter, Unset):
            restore_ended_before_filter = self.restore_ended_before_filter.isoformat()

        restore_ended_after_filter: str | Unset = UNSET
        if not isinstance(self.restore_ended_after_filter, Unset):
            restore_ended_after_filter = self.restore_ended_after_filter.isoformat()

        initiator_name_filter = self.initiator_name_filter

        name_filter = self.name_filter

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
        if restore_status_filter is not UNSET:
            field_dict["restoreStatusFilter"] = restore_status_filter
        if restore_ended_before_filter is not UNSET:
            field_dict["restoreEndedBeforeFilter"] = restore_ended_before_filter
        if restore_ended_after_filter is not UNSET:
            field_dict["restoreEndedAfterFilter"] = restore_ended_after_filter
        if initiator_name_filter is not UNSET:
            field_dict["initiatorNameFilter"] = initiator_name_filter
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EFlrAuditItemsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EFlrAuditItemsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        _restore_status_filter = d.pop("restoreStatusFilter", UNSET)
        restore_status_filter: list[EFlrItemRestoreStatus] | Unset = UNSET
        if _restore_status_filter is not UNSET:
            restore_status_filter = []
            for restore_status_filter_item_data in _restore_status_filter:
                restore_status_filter_item = EFlrItemRestoreStatus(restore_status_filter_item_data)

                restore_status_filter.append(restore_status_filter_item)

        _restore_ended_before_filter = d.pop("restoreEndedBeforeFilter", UNSET)
        restore_ended_before_filter: datetime.datetime | Unset
        if isinstance(_restore_ended_before_filter, Unset):
            restore_ended_before_filter = UNSET
        else:
            restore_ended_before_filter = isoparse(_restore_ended_before_filter)

        _restore_ended_after_filter = d.pop("restoreEndedAfterFilter", UNSET)
        restore_ended_after_filter: datetime.datetime | Unset
        if isinstance(_restore_ended_after_filter, Unset):
            restore_ended_after_filter = UNSET
        else:
            restore_ended_after_filter = isoparse(_restore_ended_after_filter)

        initiator_name_filter = d.pop("initiatorNameFilter", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        flr_audit_items_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            restore_status_filter=restore_status_filter,
            restore_ended_before_filter=restore_ended_before_filter,
            restore_ended_after_filter=restore_ended_after_filter,
            initiator_name_filter=initiator_name_filter,
            name_filter=name_filter,
        )

        flr_audit_items_filters.additional_properties = d
        return flr_audit_items_filters

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
