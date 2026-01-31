from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_backups_filters_order_column import EBackupsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupsFilters")


@_attrs_define
class BackupsFilters:
    """
    Attributes:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        platform_id_filter (UUID | Unset):
        job_id_filter (UUID | Unset):
        policy_tag_filter (str | Unset):
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET
    order_asc: bool | Unset = UNSET
    name_filter: str | Unset = UNSET
    created_after_filter: datetime.datetime | Unset = UNSET
    created_before_filter: datetime.datetime | Unset = UNSET
    platform_id_filter: UUID | Unset = UNSET
    job_id_filter: UUID | Unset = UNSET
    policy_tag_filter: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: str | Unset = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        created_after_filter: str | Unset = UNSET
        if not isinstance(self.created_after_filter, Unset):
            created_after_filter = self.created_after_filter.isoformat()

        created_before_filter: str | Unset = UNSET
        if not isinstance(self.created_before_filter, Unset):
            created_before_filter = self.created_before_filter.isoformat()

        platform_id_filter: str | Unset = UNSET
        if not isinstance(self.platform_id_filter, Unset):
            platform_id_filter = str(self.platform_id_filter)

        job_id_filter: str | Unset = UNSET
        if not isinstance(self.job_id_filter, Unset):
            job_id_filter = str(self.job_id_filter)

        policy_tag_filter = self.policy_tag_filter

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
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter
        if platform_id_filter is not UNSET:
            field_dict["platformIdFilter"] = platform_id_filter
        if job_id_filter is not UNSET:
            field_dict["jobIdFilter"] = job_id_filter
        if policy_tag_filter is not UNSET:
            field_dict["policyTagFilter"] = policy_tag_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: EBackupsFiltersOrderColumn | Unset
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EBackupsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

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

        _platform_id_filter = d.pop("platformIdFilter", UNSET)
        platform_id_filter: UUID | Unset
        if isinstance(_platform_id_filter, Unset):
            platform_id_filter = UNSET
        else:
            platform_id_filter = UUID(_platform_id_filter)

        _job_id_filter = d.pop("jobIdFilter", UNSET)
        job_id_filter: UUID | Unset
        if isinstance(_job_id_filter, Unset):
            job_id_filter = UNSET
        else:
            job_id_filter = UUID(_job_id_filter)

        policy_tag_filter = d.pop("policyTagFilter", UNSET)

        backups_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            platform_id_filter=platform_id_filter,
            job_id_filter=job_id_filter,
            policy_tag_filter=policy_tag_filter,
        )

        backups_filters.additional_properties = d
        return backups_filters

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
