from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_credentials_filters_order_column import ECredentialsFiltersOrderColumn
from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CredentialsFilters")


@_attrs_define
class CredentialsFilters:
    """
    Attributes:
        skip (int | Unset): Number of credentials records to skip.
        limit (int | Unset): Maximum number of credentials records to return.
        order_column (ECredentialsFiltersOrderColumn | Unset):
        order_asc (bool | Unset): If `true`, sorts credentials in ascending order by the `orderColumn` parameter.
        name_filter (str | Unset): Filters credentials by the `nameFilter` pattern. The pattern can match any
            credentials parameter. To substitute one or more characters, use the asterisk (*) character at the beginning
            and/or at the end.
        include_default_appliance_creds (bool | Unset): If `true`, default appliance credentials will be included in the
            response.
        type_filter (ECredentialsType | Unset): Credentials type.
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: ECredentialsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    include_default_appliance_creds: bool | Unset = UNSET
    type_filter: ECredentialsType | Unset = UNSET
    created_after_filter: datetime.datetime | Unset = UNSET
    created_before_filter: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        include_default_appliance_creds = self.include_default_appliance_creds

        type_filter: str | Unset = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        created_after_filter: str | Unset = UNSET
        if not isinstance(self.created_after_filter, Unset):
            created_after_filter = self.created_after_filter.isoformat()

        created_before_filter: str | Unset = UNSET
        if not isinstance(self.created_before_filter, Unset):
            created_before_filter = self.created_before_filter.isoformat()

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
        if include_default_appliance_creds is not UNSET:
            field_dict["includeDefaultApplianceCreds"] = include_default_appliance_creds
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: ECredentialsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ECredentialsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        include_default_appliance_creds = d.pop("includeDefaultApplianceCreds", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: ECredentialsType | Unset
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = ECredentialsType(_type_filter)

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

        credentials_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            include_default_appliance_creds=include_default_appliance_creds,
            type_filter=type_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
        )

        credentials_filters.additional_properties = d
        return credentials_filters

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
