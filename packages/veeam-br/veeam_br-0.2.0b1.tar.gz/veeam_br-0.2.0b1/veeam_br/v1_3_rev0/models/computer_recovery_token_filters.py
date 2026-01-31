from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_computer_recovery_token_filters_order_column import EComputerRecoveryTokenFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="ComputerRecoveryTokenFilters")


@_attrs_define
class ComputerRecoveryTokenFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EComputerRecoveryTokenFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        expiration_date_before (datetime.datetime | Unset):
        expiration_date_after (datetime.datetime | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EComputerRecoveryTokenFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    expiration_date_before: datetime.datetime | Unset = UNSET
    expiration_date_after: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        expiration_date_before: str | Unset = UNSET
        if not isinstance(self.expiration_date_before, Unset):
            expiration_date_before = self.expiration_date_before.isoformat()

        expiration_date_after: str | Unset = UNSET
        if not isinstance(self.expiration_date_after, Unset):
            expiration_date_after = self.expiration_date_after.isoformat()

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
        if expiration_date_before is not UNSET:
            field_dict["expirationDateBefore"] = expiration_date_before
        if expiration_date_after is not UNSET:
            field_dict["expirationDateAfter"] = expiration_date_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EComputerRecoveryTokenFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EComputerRecoveryTokenFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _expiration_date_before = d.pop("expirationDateBefore", UNSET)
        expiration_date_before: datetime.datetime | Unset
        if isinstance(_expiration_date_before, Unset):
            expiration_date_before = UNSET
        else:
            expiration_date_before = isoparse(_expiration_date_before)

        _expiration_date_after = d.pop("expirationDateAfter", UNSET)
        expiration_date_after: datetime.datetime | Unset
        if isinstance(_expiration_date_after, Unset):
            expiration_date_after = UNSET
        else:
            expiration_date_after = isoparse(_expiration_date_after)

        computer_recovery_token_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            expiration_date_before=expiration_date_before,
            expiration_date_after=expiration_date_after,
        )

        computer_recovery_token_filters.additional_properties = d
        return computer_recovery_token_filters

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
