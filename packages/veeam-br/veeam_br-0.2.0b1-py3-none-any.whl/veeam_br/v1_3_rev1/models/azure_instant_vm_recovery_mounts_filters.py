from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_instant_recovery_mount_state import EAzureInstantRecoveryMountState
from ..models.e_azure_instant_vm_recovery_mounts_filters_order_column import (
    EAzureInstantVMRecoveryMountsFiltersOrderColumn,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureInstantVMRecoveryMountsFilters")


@_attrs_define
class AzureInstantVMRecoveryMountsFilters:
    """
    Attributes:
        skip (int | Unset): Number of mounts to skip.
        limit (int | Unset): Maximum number of mounts to return.
        order_column (EAzureInstantVMRecoveryMountsFiltersOrderColumn | Unset): Sorts mounts by one of the mount
            parameters.
        order_asc (bool | Unset): Sorts mounts in ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters mounts by the `nameFilter` pattern. The pattern can match any mount
            parameter. To substitute one or more characters, use the asterisk (*) character at the beginning, at the end or
            both.
        state_filter (EAzureInstantRecoveryMountState | Unset): Mount state.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EAzureInstantVMRecoveryMountsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    state_filter: EAzureInstantRecoveryMountState | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        state_filter: str | Unset = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

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
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EAzureInstantVMRecoveryMountsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EAzureInstantVMRecoveryMountsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: EAzureInstantRecoveryMountState | Unset
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = EAzureInstantRecoveryMountState(_state_filter)

        azure_instant_vm_recovery_mounts_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            state_filter=state_filter,
        )

        azure_instant_vm_recovery_mounts_filters.additional_properties = d
        return azure_instant_vm_recovery_mounts_filters

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
