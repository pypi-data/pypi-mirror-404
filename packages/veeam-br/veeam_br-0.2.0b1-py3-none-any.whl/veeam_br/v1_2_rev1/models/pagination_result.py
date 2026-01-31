from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PaginationResult")


@_attrs_define
class PaginationResult:
    """Pagination settings.

    Attributes:
        total (int): Total number of results.
        count (int): Number of returned results.
        skip (int | Unset): Number of skipped results.
        limit (int | Unset): Maximum number of results to return.
    """

    total: int
    count: int
    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        count = self.count

        skip = self.skip

        limit = self.limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "count": count,
            }
        )
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total = d.pop("total")

        count = d.pop("count")

        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        pagination_result = cls(
            total=total,
            count=count,
            skip=skip,
            limit=limit,
        )

        pagination_result.additional_properties = d
        return pagination_result

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
